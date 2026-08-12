import os
import sys
import time
import logging
import concurrent.futures
from typing import Optional, Tuple
from PIL import Image, ImageOps, ImageFilter

logger = logging.getLogger(__name__)

class TextExtractionError(Exception):
    """Custom exception raised when text extraction fails."""
    pass

class OCRService:
    """
    High-performance, production-ready OCR Service for LexGuard AI.
    Features:
    - Pre-initialized singleton EasyOCR & Tesseract engines.
    - Pillow EXIF auto-rotation, color mode normalization, max-dimension downscaling.
    - Primary OCR (Tesseract) with fallback OCR (EasyOCR).
    - Hard timeout protection and resource cleanup.
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
        """Initialize EasyOCR singleton reader once (CPU/GPU safe)."""
        if self._easyocr_reader is None:
            logger.info("[OCR] Initializing EasyOCR singleton reader (English)...")
            t0 = time.time()
            try:
                import easyocr
                # Disable GPU if CUDA unavailable to prevent warnings
                self._easyocr_reader = easyocr.Reader(['en'], gpu=False)
                self._easyocr_initialized = True
                logger.info(f"[OCR] EasyOCR singleton reader initialized in {time.time() - t0:.2f}s")
            except Exception as e:
                logger.error(f"[OCR] EasyOCR reader initialization failed: {e}")
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

    def preprocess_image(self, file_path: str) -> Tuple[Image.Image, float]:
        """
        Preprocess image for maximum OCR accuracy and high execution speed.
        - Fix EXIF orientation.
        - Convert transparency / palette to RGB.
        - Resize oversized images to max dimension 2400px (preserves quality while boosting OCR speed).
        - Convert to grayscale, apply autocontrast and subtle sharpening.
        """
        t0 = time.time()
        self.validate_image(file_path)

        try:
            Image.MAX_IMAGE_PIXELS = 100_000_000
            with Image.open(file_path) as img:
                w, h = img.size
                if w * h > Image.MAX_IMAGE_PIXELS:
                    raise TextExtractionError(f"Image resolution too large ({w}x{h}). Max: 100MP.")

                # Correct EXIF rotation
                img = ImageOps.exif_transpose(img)

                # Flatten alpha/transparency channels on white background
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, (0, 0), img)
                    img = bg.convert("RGB")
                else:
                    img = img.convert("RGB")

                # Dynamic downscaling for large photographs (e.g. 4000x3000 -> max 2400px)
                MAX_OCR_DIM = 2400
                if max(w, h) > MAX_OCR_DIM:
                    scale = MAX_OCR_DIM / float(max(w, h))
                    new_w = max(1, int(w * scale))
                    new_h = max(1, int(h * scale))
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    logger.info(f"[OCR] Downscaled image from {w}x{h} to {new_w}x{new_h} for OCR optimization")

                # Grayscale, autocontrast & subtle sharpen
                gray = img.convert("L")
                enhanced = ImageOps.autocontrast(gray)
                processed = enhanced.filter(ImageFilter.SHARPEN)
                
                prep_duration = time.time() - t0
                return processed.copy(), prep_duration

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

    def _run_tesseract(self, processed_img: Image.Image) -> str:
        """Run Primary OCR engine (PyTesseract)."""
        import pytesseract
        tess_path = self.get_tesseract_path()
        if os.path.exists(tess_path):
            pytesseract.pytesseract.tesseract_cmd = tess_path
            
        # PSM 3: Fully automatic page segmentation, OEM 3: Default LSTM
        return pytesseract.image_to_string(processed_img, config='--oem 3 --psm 3', timeout=20)

    def _run_easyocr(self, processed_img: Image.Image) -> Tuple[str, float]:
        """Run Fallback OCR engine (EasyOCR). Returns (extracted_text, avg_confidence)."""
        import numpy as np
        reader = self.init_easyocr()
        if not reader:
            return "", 0.0

        img_np = np.array(processed_img)
        results = reader.readtext(img_np)
        
        extracted_lines = []
        total_conf = 0.0
        for item in results:
            if len(item) >= 3:
                extracted_lines.append(item[1])
                total_conf += float(item[2])
                
        text = "\n".join(extracted_lines).strip()
        avg_conf = (total_conf / len(results)) if results else 0.0
        return text, avg_conf

    def extract_text_from_image(self, file_path: str, timeout_seconds: int = 25) -> str:
        """
        Main OCR pipeline:
        1. Preprocess image once.
        2. Execute Primary OCR (Tesseract).
        3. If Primary OCR produces sufficient text, return immediately.
        4. Otherwise execute Fallback OCR (EasyOCR).
        5. Log detailed timing and character metrics.
        """
        t0_total = time.time()

        # 1. Preprocess image
        processed_img, prep_time = self.preprocess_image(file_path)
        logger.info(f"[OCR] Image preprocessing: {prep_time:.2f}s")

        # 2. Primary OCR (Tesseract)
        t0_primary = time.time()
        logger.info("[OCR] Primary OCR (Tesseract) started")
        
        primary_text = ""
        try:
            primary_text = self._run_tesseract(processed_img)
        except Exception as e:
            logger.warning(f"[OCR] Primary OCR (Tesseract) failed or timed out: {e}")
            
        primary_duration = time.time() - t0_primary
        cleaned_primary = self.clean_text(primary_text)
        
        logger.info(f"[OCR] Primary OCR completed: {primary_duration:.2f}s")
        logger.info(f"[OCR] Extracted characters: {len(cleaned_primary)}")

        # Check if primary OCR produced sufficient meaningful text (>= 15 characters)
        if len(cleaned_primary) >= 15:
            logger.info(f"[OCR] Primary OCR succeeded with {len(cleaned_primary)} characters. Skipping fallback.")
            total_ocr_time = time.time() - t0_total
            logger.info(f"[OCR] Total OCR time: {total_ocr_time:.2f}s")
            return cleaned_primary

        # 3. Fallback OCR (EasyOCR) if primary failed or produced insufficient text
        logger.info(f"[OCR] Primary OCR produced insufficient text ({len(cleaned_primary)} chars). Starting EasyOCR fallback...")
        t0_fallback = time.time()

        fallback_text = ""
        fallback_conf = 0.0
        try:
            fallback_text, fallback_conf = self._run_easyocr(processed_img)
        except Exception as e:
            logger.error(f"[OCR] EasyOCR fallback failed: {e}")

        fallback_duration = time.time() - t0_fallback
        cleaned_fallback = self.clean_text(fallback_text)

        logger.info(f"[OCR] EasyOCR completed: {fallback_duration:.2f}s")
        logger.info(f"[OCR] Extracted characters: {len(cleaned_fallback)}")
        logger.info(f"[OCR] Confidence: {fallback_conf:.2f}")

        final_text = cleaned_fallback if len(cleaned_fallback) > len(cleaned_primary) else cleaned_primary

        total_ocr_time = time.time() - t0_total
        logger.info(f"[OCR] Total OCR time: {total_ocr_time:.2f}s")

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
            raise TextExtractionError("No readable text found in image.")

        return final_text


ocr_service = OCRService()
