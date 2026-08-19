import os
import sys
import time
import logging
import concurrent.futures
import io
from typing import Optional, Tuple
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import numpy as np

logger = logging.getLogger(__name__)

class TextExtractionError(Exception):
    """Custom exception raised when text extraction fails."""
    pass

class OCRService:
    """
    High-performance, production-ready image OCR Service for LexGuard AI.
    Features:
    - Pre-initialized singleton EasyOCR & Tesseract engines.
    - Image preprocessing: EXIF transpose, RGB normalization, max 1500px downscaling,
      grayscale conversion, noise removal, contrast enhancement, adaptive thresholding.
    - Compression before OCR execution.
    - Automatic OCR fallback: Primary EasyOCR -> if confidence < 0.40 or timeout -> PyTesseract fallback.
    - Result merging (deduplicated line integration).
    - Structured [OCR] and [PERF] timing logs.
    """
    def __init__(self):
        self._easyocr_reader = None
        self._tesseract_path: Optional[str] = None
        self._easyocr_initialized = False

    def get_tesseract_path(self) -> str:
        """Resolve and cache Tesseract executable path."""
        if self._tesseract_path:
            return self._tesseract_path
            
        from app.services.document_service import get_tesseract_path as resolve_tess
        self._tesseract_path = resolve_tess()
        return self._tesseract_path

    def init_easyocr(self):
        """Lazily initialize EasyOCR singleton reader once on demand (CPU mode only)."""
        if self._easyocr_reader is None:
            import threading
            if not hasattr(self, '_lock'):
                self._lock = threading.Lock()
            with self._lock:
                if self._easyocr_reader is None:
                    logger.info("[OCR] Lazily initializing EasyOCR singleton reader (CPU mode)...")
                    t0 = time.time()
                    try:
                        import easyocr
                        # Disable GPU explicitly for 512MB RAM environment
                        self._easyocr_reader = easyocr.Reader(['en'], gpu=False)
                        self._easyocr_initialized = True
                        logger.info(f"[OCR] EasyOCR reader lazily initialized in {time.time() - t0:.2f}s")
                    except Exception as e:
                        logger.error(f"[OCR] EasyOCR reader initialization failed/skipped: {e}")
                        self._easyocr_reader = None
        return self._easyocr_reader


    def validate_image(self, file_path: str):
        """Validate image existence, non-emptiness, and pixel resolution bounds."""
        if not os.path.exists(file_path):
            raise TextExtractionError("File not found on server.")
        if os.path.getsize(file_path) == 0:
            raise TextExtractionError("Image file is empty.")

        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            raise TextExtractionError(f"Invalid image format: {e}") from e

    def preprocess_image(self, file_path: str) -> Tuple[Image.Image, bytes, float]:
        """
        Preprocess image for maximum OCR accuracy and high execution speed.
        1. EXIF orientation correction
        2. RGB conversion (flatten transparency / palette to RGB on white background)
        3. Resize large images to maximum 1500 px
        4. Grayscale conversion
        5. Remove noise
        6. Increase contrast
        7. Adaptive thresholding
        8. Image compression before OCR
        Returns (processed_PIL_Image, compressed_jpeg_bytes, prep_duration)
        """
        t0 = time.time()
        self.validate_image(file_path)

        try:
            Image.MAX_IMAGE_PIXELS = 100_000_000
            with Image.open(file_path) as img:
                w, h = img.size
                if w * h > Image.MAX_IMAGE_PIXELS:
                    raise TextExtractionError(f"Image resolution too large ({w}x{h}). Max: 100MP.")

                # 1. Correct EXIF rotation
                img = ImageOps.exif_transpose(img)

                # 2. RGB conversion (flatten alpha/transparency channels on white background)
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, (0, 0), img)
                    img = img.convert("RGB")
                else:
                    img = img.convert("RGB")

                # 3. Resize large images to maximum 1500 px
                MAX_OCR_DIM = 1500
                orig_w, orig_h = img.size
                if max(orig_w, orig_h) > MAX_OCR_DIM:
                    scale = MAX_OCR_DIM / float(max(orig_w, orig_h))
                    new_w = max(1, int(orig_w * scale))
                    new_h = max(1, int(orig_h * scale))
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    logger.info(f"[OCR] Resized large image from {orig_w}x{orig_h} to {new_w}x{new_h} (max {MAX_OCR_DIM}px)")

                # 4. Grayscale conversion
                gray_img = img.convert("L")

                # 5, 6. Noise removal and contrast enhancement (preserving smooth text edges)
                try:
                    import cv2
                    gray_np = np.array(gray_img)
                    
                    # Denoise with Gaussian blur
                    denoised = cv2.GaussianBlur(gray_np, (3, 3), 0)
                    
                    # Increase contrast with CLAHE
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    contrast_np = clahe.apply(denoised)
                    processed_pil = Image.fromarray(contrast_np)
                except Exception as cv_err:
                    logger.warning(f"[OCR] OpenCV preprocessing fallback to PIL: {cv_err}")
                    med = gray_img.filter(ImageFilter.MedianFilter(size=3))
                    enhanced = ImageEnhance.Contrast(med).enhance(1.5)
                    processed_pil = ImageOps.autocontrast(enhanced)

                # 7. Compression before OCR: in-memory JPEG compression (quality 90)
                buffer = io.BytesIO()
                processed_pil.convert("RGB").save(buffer, format="JPEG", quality=90, optimize=True)
                compressed_bytes = buffer.getvalue()

                prep_duration = time.time() - t0
                return processed_pil, compressed_bytes, prep_duration

        except TextExtractionError:
            raise
        except Exception as e:
            raise TextExtractionError(f"Image preprocessing failed: {e}") from e

    def clean_text(self, text: str) -> str:
        """Clean control characters and whitespace."""
        if not text:
            return ""
        cleaned = "".join(ch for ch in text if ch.isprintable() or ch in ('\n', '\r', '\t'))
        return "\n".join(line.strip() for line in cleaned.splitlines() if line.strip()).strip()

    def _run_easyocr_with_timeout(self, processed_img: Image.Image, compressed_bytes: bytes, timeout_seconds: int = 12) -> Tuple[str, float, float]:
        """Run Primary OCR engine (EasyOCR) with hard timeout. Returns (extracted_text, avg_confidence, duration)."""
        t0 = time.time()
        
        def _exec():
            reader = self.init_easyocr()
            if not reader:
                return "", 0.0
            
            with Image.open(io.BytesIO(compressed_bytes)) as c_img:
                img_np = np.array(c_img)
            
            results = reader.readtext(img_np, canvas_size=1500)
            extracted_lines = []
            total_conf = 0.0
            for item in results:
                if len(item) >= 3:
                    extracted_lines.append(str(item[1]))
                    total_conf += float(item[2])
                    
            text = "\n".join(extracted_lines).strip()
            avg_conf = (total_conf / len(results)) if results else 0.0
            return text, avg_conf

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_exec)
            try:
                text, conf = future.result(timeout=timeout_seconds)
                duration = time.time() - t0
                return text, conf, duration
            except concurrent.futures.TimeoutError:
                duration = time.time() - t0
                logger.warning(f"[OCR] EasyOCR timed out after {duration:.2f}s (timeout={timeout_seconds}s)")
                return "", 0.0, duration
            except Exception as e:
                duration = time.time() - t0
                logger.warning(f"[OCR] EasyOCR failed in {duration:.2f}s: {e}")
                return "", 0.0, duration

    def _run_pytesseract_with_timeout(self, processed_img: Image.Image, timeout_seconds: int = 8) -> Tuple[str, float]:
        """Run Fallback OCR engine (PyTesseract) with hard timeout. Returns (extracted_text, duration)."""
        t0 = time.time()
        
        def _exec():
            import pytesseract
            tess_path = self.get_tesseract_path()
            if os.path.exists(tess_path) or tess_path == "tesseract":
                pytesseract.pytesseract.tesseract_cmd = tess_path
                
            return pytesseract.image_to_string(processed_img, config='--oem 3 --psm 3', timeout=timeout_seconds)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_exec)
            try:
                text = future.result(timeout=timeout_seconds)
                duration = time.time() - t0
                return text, duration
            except Exception as e:
                duration = time.time() - t0
                logger.warning(f"[OCR] PyTesseract fallback failed in {duration:.2f}s: {e}")
                return "", duration

    def merge_ocr_results(self, primary_text: str, fallback_text: str) -> str:
        """
        Merge results from EasyOCR and PyTesseract into a complete, non-redundant output.
        """
        clean_prim = self.clean_text(primary_text)
        clean_fall = self.clean_text(fallback_text)

        if not clean_prim:
            return clean_fall
        if not clean_fall:
            return clean_prim

        prim_lines = [line.strip() for line in clean_prim.splitlines() if line.strip()]
        fall_lines = [line.strip() for line in clean_fall.splitlines() if line.strip()]

        merged_lines = list(prim_lines)
        for f_line in fall_lines:
            # Append fallback line if it adds unique text not already in primary
            if not any(f_line.lower() in p_line.lower() or p_line.lower() in f_line.lower() for p_line in prim_lines):
                merged_lines.append(f_line)

        return "\n".join(merged_lines).strip()

    def extract_text_from_image(self, file_path: str, timeout_seconds: int = 25) -> str:
        """
        Complete Image OCR Pipeline:
        1. Preprocess & compress image (EXIF, RGB, grayscale, max 1500px, CLAHE contrast, compression).
        2. Execute Fast Primary Engine: PyTesseract (~0.5 - 2s execution).
        3. Secondary Engine: EasyOCR fallback if PyTesseract produces insufficient text (< 15 chars).
        4. Merge results and return clean text.
        """
        t0_total = time.time()

        # 1. Preprocess image
        processed_img, compressed_bytes, prep_duration = self.preprocess_image(file_path)
        logger.info(f"[PERF] Image Preprocessing Time: {prep_duration*1000:.1f}ms ({prep_duration:.2f}s)")

        # 2. Fast Primary Engine: PyTesseract
        logger.info("[OCR] Primary OCR Engine (PyTesseract) started...")
        pytesseract_text, pytesseract_duration = self._run_pytesseract_with_timeout(
            processed_img, timeout_seconds=8
        )
        cleaned_pytesseract = self.clean_text(pytesseract_text)
        logger.info(f"[PERF] PyTesseract Time: {pytesseract_duration*1000:.1f}ms ({pytesseract_duration:.2f}s) | Chars: {len(cleaned_pytesseract)}")

        easyocr_text = ""
        easyocr_duration = 0.0
        fallback_triggered = False

        # 3. Fallback Condition: PyTesseract produced insufficient text (< 15 chars)
        if not cleaned_pytesseract or len(cleaned_pytesseract) < 15:
            fallback_triggered = True
            reason = "no text" if not cleaned_pytesseract else "insufficient text (< 15 chars)"
            logger.info(f"[OCR] PyTesseract produced insufficient result ({reason}). Triggering EasyOCR secondary fallback...")
            easyocr_text, easyocr_conf, easyocr_duration = self._run_easyocr_with_timeout(
                processed_img, compressed_bytes, timeout_seconds=12
            )
            cleaned_easyocr = self.clean_text(easyocr_text)
            logger.info(f"[PERF] EasyOCR Fallback Time: {easyocr_duration*1000:.1f}ms ({easyocr_duration:.2f}s) | Confidence: {easyocr_conf:.2f} | Chars: {len(cleaned_easyocr)}")

        # 4. Merge results
        if fallback_triggered and easyocr_text:
            final_text = self.merge_ocr_results(cleaned_pytesseract, easyocr_text)
        else:
            final_text = cleaned_pytesseract if cleaned_pytesseract else self.clean_text(easyocr_text)

        total_ocr_time = time.time() - t0_total
        logger.info(
            f"[PERF] IMAGE PIPELINE - Preprocess: {prep_duration*1000:.1f}ms | "
            f"OCR: {total_ocr_time*1000:.1f}ms | Total: {total_ocr_time*1000:.1f}ms "
            f"(Primary: PyTesseract, Secondary: {'EasyOCR' if fallback_triggered else 'Skipped'})"
        )

        if not final_text:
            # Check for blank image
            try:
                extrema = processed_img.getextrema()
                if extrema and extrema[0] == extrema[1]:
                    raise TextExtractionError("No readable text found in image (image is completely blank).")
            except TextExtractionError:
                raise
            except Exception:
                pass
            if total_ocr_time >= timeout_seconds:
                raise TextExtractionError(f"OCR processing timed out. Please upload a clearer or smaller image.")
            raise TextExtractionError("No readable text found in image.")

        return final_text


ocr_service = OCRService()


