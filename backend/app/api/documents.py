import os
import uuid
import logging
import mimetypes
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from typing import List, Optional
import traceback

from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.api.deps import get_current_user
from app.core.config import settings
from app.services.document_service import extract_text, get_file_extension, validate_file, get_user_storage_usage_mb, get_supabase
from app.services.groq_service import groq_service

router = APIRouter()
logger = logging.getLogger(__name__)


def update_document_status(db, document_id: str, status: str, error_message: Optional[str] = None):
    """Helper to update document status in both Firestore and PostgreSQL."""
    try:
        db.update_document(document_id, {
            "status": status,
            "error_message": error_message
        })
    except Exception as fe:
        logger.error(f"Failed to update document status in Firestore: {fe}")
        
    conn = None
    try:
        conn = db._get_pg_conn()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE documents SET status = %s, error_message = %s WHERE id = %s",
                    (status, error_message, document_id)
                )
                conn.commit()
                logger.info(f"Document {document_id} status updated to '{status}' in PostgreSQL")
            finally:
                cur.close()
    except Exception as pe:
        logger.error(f"Failed to update document status in PostgreSQL: {pe}")
    finally:
        if conn:
            conn.close()


async def run_ai_analysis(document_id: str):
    """Background task: extract text from document and run Groq AI analysis."""
    import time
    from app.services.firebase_service import firebase_service
    from app.services.document_service import TextExtractionError
    db = firebase_service
    
    t0_total = time.time()
    
    try:
        doc_data = db.get_document(document_id)
        if not doc_data:
            logger.error(f"Document {document_id} not found for analysis")
            return
            
        doc = Document(**doc_data)
        
        # Calculate upload overhead duration
        uploaded_at_str = doc_data.get("uploaded_at")
        t_upload = 0.0
        if uploaded_at_str:
            try:
                from datetime import datetime, timezone
                up_dt = datetime.fromisoformat(uploaded_at_str.replace('Z', '+00:00'))
                t_upload = max(0.0, (datetime.now(timezone.utc) - up_dt).total_seconds())
            except Exception:
                pass

        # Step 1: Extract text
        update_document_status(db, document_id, "extracting")
        logger.info(f"Analysis started for document {document_id}")
        
        # Check if file exists locally, if not download from Storage
        local_path = doc.path
        if not local_path or not os.path.exists(local_path):
            local_dir = settings.UPLOAD_DIR
            local_path = os.path.join(local_dir, f"{document_id}.{doc.type}")
            os.makedirs(local_dir, exist_ok=True)
            download_success = False
            
            supabase = get_supabase()
            if supabase:
                storage_path = f"users/{doc.user_id}/documents/{document_id}.{doc.type}"
                try:
                    res = supabase.storage.from_("legal-documents").download(storage_path)
                    with open(local_path, "wb") as f:
                        f.write(res)
                    download_success = True
                except Exception as e:
                    logger.error(f"Supabase download failed: {e}")
                    download_success = False
                    
            if not download_success and not os.path.exists(local_path):
                logger.error(f"Failed to access or download file for document {document_id}")
                update_document_status(db, document_id, "failed", "File content unavailable for text extraction.")
                return
            db.update_document(document_id, {"path": local_path})
            doc.path = local_path
            
        file_ext = get_file_extension(doc.name)
        fmt_tag = file_ext.upper()
        logger.info(f"[{fmt_tag}] File received: {doc.name} | Size: {doc.size_in_mb} MB")
        logger.info(f"[{fmt_tag}] Extraction started for document_id={document_id}")
        
        # Text Extraction phase
        t0_extract = time.time()
        try:
            import asyncio
            extracted_text = await asyncio.to_thread(extract_text, local_path, file_ext)
            
            MIN_TEXT_LENGTH = 10
            if not extracted_text or not extracted_text.strip() or len(extracted_text.strip()) < MIN_TEXT_LENGTH:
                if file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp',
                                  'image/jpeg', 'image/png', 'image/jpg', 'image/bmp', 'image/tiff', 'image/webp']:
                    raise TextExtractionError("No readable text found in image.")
                elif file_ext in ['docx', 'doc']:
                    raise TextExtractionError("Could not extract readable text from the DOCX file.")
                else:
                    raise TextExtractionError("Unable to extract readable text from document.")
        except TextExtractionError as ete:
            error_reason = str(ete)
            update_document_status(db, document_id, "failed", error_reason)
            logger.error(f"[{fmt_tag}] Text extraction failed for {document_id}: {error_reason}")
            return
        except Exception as ex:
            error_reason = "Could not extract readable text from document." if file_ext not in ['docx', 'doc'] else "Could not extract readable text from the DOCX file."
            update_document_status(db, document_id, "failed", error_reason)
            logger.error(f"[{fmt_tag}] Text extraction failed for {document_id}: {type(ex).__name__}: {ex}", exc_info=True)
            return
            
        t_extract = time.time() - t0_extract
        logger.info(f"[{fmt_tag}] Extraction completed | Extracted character count: {len(extracted_text)} | [PERF] Text extraction: {t_extract:.2f}s")
        
        db.update_document(document_id, {
            "extracted_text": extracted_text,
            "status": "analyzing"
        })
        
        # Step 1.5: Vector Indexing
        try:
            from app.services.vector_service import vector_service
            await vector_service.create_vector_index(document_id, extracted_text)
        except Exception as e:
            logger.error(f"Vector indexing failed for {document_id}: {e}")
        
        # Step 2: Run Groq AI analysis
        t0_llm = time.time()
        try:
            logger.info(f"[{fmt_tag}] AI analysis started for document {document_id}")
            analysis_result = await groq_service.analyze_document(extracted_text)
            t_llm = time.time() - t0_llm
            logger.info(f"[{fmt_tag}] AI analysis completed | [PERF] LLM: {t_llm:.2f}s")
        except Exception as e:
            logger.error(f"[{fmt_tag}] Groq AI analysis failed for document {document_id}: {type(e).__name__} - {e}", exc_info=True)
            analysis_result = groq_service._fallback_rule_based_analysis(extracted_text)

        
        # Step 3: Save analysis results to Document
        t0_db = time.time()
        try:
            db.update_document(document_id, {
                "risk_score": analysis_result.get("risk_score", 0),
                "risk_level": analysis_result.get("risk_level", "Medium"),
                "summary": analysis_result.get("summary", ""),
                "document_type": analysis_result.get("document_type", "Unknown"),
                "status": "completed",
                "error_message": None,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            })
        except Exception as fe:
            logger.error(f"Error updating document status to completed for {document_id}: {fe}")
            
        analysis_data = {
            "document_id": document_id,
            "risk_level": analysis_result.get("risk_level", "Medium"),
            "risk_score": analysis_result.get("risk_score", 0),
            "summary": analysis_result.get("summary", ""),
            "ai_confidence": 0.85,
            "parties": analysis_result.get("parties", []),
            "important_dates": analysis_result.get("important_dates", []),
            "recommendations": analysis_result.get("recommendations", []),
            "raw_analysis_data": analysis_result,
        }
        try:
            db.save_analysis(document_id, analysis_data)
        except Exception as se:
            logger.warning(f"save_analysis warning for {document_id}: {se}")
        
        try:
            db.delete_document_clauses(document_id)
            for clause_data in analysis_result.get("clauses", []):
                db.save_clause({
                    "document_id": document_id,
                    "title": clause_data.get("title", "Untitled Clause"),
                    "content": clause_data.get("content", ""),
                    "summary": clause_data.get("explanation", clause_data.get("summary", "")),
                    "risk_level": clause_data.get("risk_level", "Low"),
                    "mitigation_advice": clause_data.get("mitigation_advice", ""),
                })
        except Exception as ce:
            logger.warning(f"save_clauses warning for {document_id}: {ce}")
            
        # Dual-write to Supabase PostgreSQL database
        conn = None
        try:
            import json
            conn = db._get_pg_conn()
            if conn:
                cur = conn.cursor()
                try:
                    cur.execute("""
                        UPDATE documents 
                        SET status = %s, 
                            extracted_text = %s, 
                            document_type = %s, 
                            risk_score = %s, 
                            risk_level = %s, 
                            summary = %s, 
                            analyzed_at = %s,
                            error_message = NULL
                        WHERE id = %s
                    """, (
                        "completed",
                        extracted_text,
                        analysis_result.get("document_type", "Unknown"),
                        analysis_result.get("risk_score", 0),
                        analysis_result.get("risk_level", "Medium"),
                        analysis_result.get("summary", ""),
                        datetime.now(timezone.utc),
                        document_id
                    ))
                    
                    cur.execute("""
                        INSERT INTO analysis (document_id, risk_level, risk_score, summary, ai_confidence, parties, important_dates, recommendations, raw_analysis_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id) DO UPDATE SET
                            risk_level = EXCLUDED.risk_level,
                            risk_score = EXCLUDED.risk_score,
                            summary = EXCLUDED.summary,
                            ai_confidence = EXCLUDED.ai_confidence,
                            parties = EXCLUDED.parties,
                            important_dates = EXCLUDED.important_dates,
                            recommendations = EXCLUDED.recommendations,
                            raw_analysis_data = EXCLUDED.raw_analysis_data
                    """, (
                        document_id,
                        analysis_result.get("risk_level", "Medium"),
                        analysis_result.get("risk_score", 0),
                        analysis_result.get("summary", ""),
                        0.85,
                        json.dumps(analysis_result.get("parties", [])),
                        json.dumps(analysis_result.get("important_dates", [])),
                        json.dumps(analysis_result.get("recommendations", [])),
                        json.dumps(analysis_result)
                    ))
                    
                    cur.execute("DELETE FROM clauses WHERE document_id = %s", (document_id,))
                    for clause_data in analysis_result.get("clauses", []):
                        cur.execute("""
                            INSERT INTO clauses (document_id, title, content, summary, risk_level, mitigation_advice)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            document_id,
                            clause_data.get("title", "Untitled Clause"),
                            clause_data.get("content", ""),
                            clause_data.get("explanation", clause_data.get("summary", "")),
                            clause_data.get("risk_level", "Low"),
                            clause_data.get("mitigation_advice", "")
                        ))
                        
                    conn.commit()
                except Exception as tx_err:
                    conn.rollback()
                    raise tx_err
                finally:
                    cur.close()
            else:
                raise RuntimeError("Could not connect to PostgreSQL")
        except Exception as pg_err:
            logger.warning(f"Failed to dual-write analysis/clauses to PostgreSQL: {pg_err} (non-fatal)")
        finally:
            if conn:
                conn.close()
                
        t_db = time.time() - t0_db
        logger.info(f"[PERF] Database: {t_db:.2f}s")
        
        t_total = time.time() - t0_total
        logger.info(
            f"[PERF] Full Pipeline Breakdown for Document {document_id}:\n"
            f"  - Upload Time: {t_upload:.2f}s\n"
            f"  - Text/OCR Extraction Time: {t_extract:.2f}s\n"
            f"  - AI Analysis Time: {t_llm:.2f}s\n"
            f"  - Total Processing Time: {t_total:.2f}s"
        )
        
    except Exception as e:
        logger.error(f"Background analysis error for {document_id}: {e}", exc_info=True)
        try:
            update_document_status(db, document_id, "failed", str(e) or "Unsupported file structure")
        except Exception as update_err:
            logger.error(f"Failed to update document status to failed: {update_err}")



@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document and trigger AI analysis in the background."""
    # Validate file
    file_content = await file.read()
    logger.info(f"File received: {file.filename}")
    
    is_valid, error_msg = validate_file(file.filename, len(file_content))
    if not is_valid:
        logger.warning(f"File validation failed for {file.filename}: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
        
    size_mb = round(len(file_content) / (1024 * 1024), 2)
    logger.info(f"Starting upload for file: {file.filename}, size: {size_mb} MB")
    
    import asyncio
    try:
        used_storage_mb = await asyncio.wait_for(
            asyncio.to_thread(get_user_storage_usage_mb, current_user.id),
            timeout=2.0
        )
    except Exception as e:
        logger.error(f"Timeout/Error fetching storage usage in upload: {e}")
        used_storage_mb = 0.0
    
    if used_storage_mb + size_mb > 20.0:
        logger.warning(f"Storage limit reached for user {current_user.id}")
        raise HTTPException(status_code=400, detail="Storage limit reached. Delete files to continue.")
    
    # Generate unique ID and save file locally first
    doc_id = str(uuid.uuid4())
    file_ext = get_file_extension(file.filename)
    safe_filename = f"{doc_id}.{file_ext}"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Upload to Supabase Storage Bucket: 'legal-documents'
    remote_path = f"users/{current_user.id}/documents/{doc_id}.{file_ext}"
    mime_type, _ = mimetypes.guess_type(file.filename)

    supabase = get_supabase()
    upload_error = None
    try:
        with open(file_path, "rb") as f:
            supabase.storage.from_("legal-documents").upload(
                file=f,
                path=remote_path,
                file_options={"content-type": mime_type or "application/octet-stream"}
            )
        download_url = supabase.storage.from_("legal-documents").get_public_url(remote_path)
        logger.info(f"File stored in Supabase storage: {remote_path}")
    except Exception as e:
        logger.warning(f"Supabase upload warning (non-fatal): {e}")
        upload_error = None
        download_url = ""
        
    # Store file URL in PostgreSQL
    status = "failed" if upload_error else "pending"
    error_message = upload_error
    
    conn = None
    try:
        conn = db._get_pg_conn()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO documents (id, user_id, name, path, type, size_in_mb, status, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (doc_id, current_user.id, file.filename, download_url, file_ext, size_mb, status, error_message))
                conn.commit()
            finally:
                cur.close()
            logger.info(f"Successfully inserted document {doc_id} into PostgreSQL")
        else:
            logger.error("Failed to get Postgres connection in upload_document")
    except Exception as e:
        logger.error(f"Failed to save document to PostgreSQL: {e}")
    finally:
        if conn:
            conn.close()
    
    # Create DB record in Firestore (Keep existing logic running parallel for now)
    doc_data = {
        "id": doc_id,
        "name": file.filename,
        "path": file_path,
        "download_url": download_url or "",
        "type": file_ext,
        "size_in_mb": size_mb,
        "status": status,
        "error_message": error_message,
        "user_id": current_user.id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "analyzed_at": None,
        "extracted_text": None,
        "document_type": None,
        "risk_score": None,
        "risk_level": None,
        "summary": None
    }
    
    db.create_document(doc_data)
    
    if not upload_error:
        # Trigger background analysis
        background_tasks.add_task(run_ai_analysis, doc_id)
        
    return {
        "success": True,
        "message": "Document uploaded. AI analysis started." if not upload_error else "Document upload failed.",
        "document": {
            "id": doc_id,
            "name": file.filename,
            "type": file_ext,
            "size_mb": size_mb,
            "status": status,
            "error_message": error_message,
            "uploaded_at": doc_data["uploaded_at"]
        }
    }


@router.get("/history")
async def get_documents(
    request: Request,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all documents for the current user."""
    documents = db.get_user_documents(current_user.id)
    
    return {
        "success": True,
        "documents": [
            {
                "id": doc["id"],
                "name": doc["name"],
                "path": str(request.url_for("download_document", document_id=doc["id"])),
                "download_url": doc.get("download_url") or str(request.url_for("download_document", document_id=doc["id"])),
                "type": doc.get("type"),
                "size_mb": doc.get("size_in_mb"),
                "status": doc.get("status"),
                "error_message": doc.get("error_message"),
                "risk_score": doc.get("risk_score"),
                "risk_level": doc.get("risk_level"),
                "summary": doc.get("summary"),
                "document_type": doc.get("document_type"),
                "uploaded_at": doc.get("uploaded_at"),
                "analyzed_at": doc.get("analyzed_at"),
            }
            for doc in documents
        ]
    }


@router.get("/{document_id}/download", name="download_document")
async def download_document(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the original uploaded document."""
    doc_data = db.get_document(document_id)
    if not doc_data or doc_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    local_path = doc_data.get("path")
    if not local_path or not os.path.exists(local_path):
        # Fallback: Download from Firebase Storage if missing locally
        local_dir = settings.UPLOAD_DIR
        local_path = os.path.join(local_dir, f"{document_id}.{doc_data.get('type')}")
        os.makedirs(local_dir, exist_ok=True)
        storage_path = f"users/{current_user.id}/documents/{document_id}.{doc_data.get('type')}"
        supabase = get_supabase()
        try:
            res = supabase.storage.from_("legal-documents").download(storage_path)
            with open(local_path, "wb") as f:
                f.write(res)
            download_success = True
        except Exception as e:
            print(f"Supabase download failed: {e}")
            download_success = False
        if not download_success:
            raise HTTPException(status_code=404, detail="Original document file is missing")
        db.update_document(document_id, {"path": local_path})

    mime_type, _ = mimetypes.guess_type(local_path)
    return FileResponse(
        path=local_path,
        filename=doc_data.get("name"),
        media_type=mime_type or "application/octet-stream",
    )


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific document with full details."""
    doc_data = db.get_document(document_id)
    if not doc_data or doc_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get analysis from Firestore
    analysis = db.get_analysis(document_id)
    # Get clauses from Firestore
    clauses = db.get_clauses(document_id)
    
    return {
        "success": True,
        "document": {
            "id": doc_data["id"],
            "name": doc_data["name"],
            "type": doc_data["type"],
            "size_mb": doc_data["size_in_mb"],
            "status": doc_data["status"],
            "error_message": doc_data.get("error_message"),
            "risk_score": doc_data.get("risk_score"),
            "risk_level": doc_data.get("risk_level"),
            "summary": doc_data.get("summary"),
            "document_type": doc_data.get("document_type"),
            "extracted_text": doc_data.get("extracted_text"),
            "uploaded_at": doc_data["uploaded_at"],
            "analyzed_at": doc_data.get("analyzed_at"),
        },
        "analysis": {
            "risk_level": analysis.get("risk_level"),
            "risk_score": analysis.get("risk_score"),
            "summary": analysis.get("summary"),
            "ai_confidence": analysis.get("ai_confidence", 0.85),
            "parties": analysis.get("parties") or [],
            "important_dates": analysis.get("important_dates") or [],
            "recommendations": analysis.get("recommendations") or [],
            "raw_data": analysis.get("raw_analysis_data") or {},
        } if analysis else None,
        "clauses": [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "content": c.get("content"),
                "summary": c.get("summary"),
                "risk_level": c.get("risk_level"),
                "mitigation_advice": c.get("mitigation_advice"),
            }
            for c in clauses
        ],
    }


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll document analysis status."""
    doc_data = db.get_document(document_id)
    if not doc_data or doc_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "success": True,
        "status": doc_data.get("status"),
        "error_message": doc_data.get("error_message"),
        "risk_score": doc_data.get("risk_score"),
        "risk_level": doc_data.get("risk_level"),
    }


@router.get("/{document_id}/export")
async def export_report(
    request: Request,
    document_id: str,
    format: str = "pdf",
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download a report in the requested format."""
    from app.services.report_service import report_service
    
    doc_data = db.get_document(document_id)
    if not doc_data or doc_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    analysis = db.get_analysis(document_id)
    clauses = db.get_clauses(document_id)
    
    if not analysis:
        raise HTTPException(status_code=400, detail="Document has not been analyzed yet")
    
    format = format.lower()
    valid_formats = {"pdf", "txt", "docx", "json", "md", "markdown"}
    if format not in valid_formats:
        raise HTTPException(status_code=400, detail="Unsupported report format")

    report_dir = os.path.join(settings.UPLOAD_DIR, "reports")
    os.makedirs(report_dir, exist_ok=True)
    file_extension = "pdf" if format == "pdf" else ("docx" if format == "docx" else ("md" if format in {"md", "markdown"} else ("json" if format == "json" else "txt")))
    report_filename = f"LexGuard_Analysis_{document_id}.{file_extension}"
    report_path = os.path.join(report_dir, report_filename)

    summary_text = doc_data.get("summary") or analysis.get("summary") or "No summary available."
    analysis_dict = {
        "risk_level": doc_data.get("risk_level"),
        "risk_score": doc_data.get("risk_score"),
        "summary": summary_text,
        "parties": analysis.get("parties") or [],
        "recommendations": analysis.get("recommendations") or [],
        "document_type": doc_data.get("document_type"),
        "uploaded_at": doc_data.get("uploaded_at"),
    }
    
    clauses_list = [
        {
            "title": c.get("title"),
            "summary": c.get("summary"),
            "risk_level": c.get("risk_level"),
            "mitigation_advice": c.get("mitigation_advice")
        }
        for c in clauses
    ]

    user_details = {
        "name": getattr(current_user, "full_name", None) or "",
        "email": current_user.email,
        "id": current_user.id,
    }

    try:
        if format == "pdf":
            report_service.generate_document_report(doc_data.get("name"), analysis_dict, clauses_list, report_path, user_details)
            media_type = "application/pdf"
        elif format == "docx":
            report_service.generate_document_report_docx(doc_data.get("name"), analysis_dict, clauses_list, report_path, user_details)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif format == "json":
            report_service.generate_document_report_json(doc_data.get("name"), analysis_dict, clauses_list, report_path, user_details)
            media_type = "application/json"
        elif format in {"md", "markdown"}:
            report_service.generate_document_report_markdown(doc_data.get("name"), analysis_dict, clauses_list, report_path, user_details)
            media_type = "text/markdown"
        else:
            report_service.generate_document_report_text(doc_data.get("name"), analysis_dict, clauses_list, report_path, user_details)
            media_type = "text/plain"
    except Exception as e:
        logger.error(f"Failed to generate report for document={document_id} format={format}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e) or "Report generation failed")

    if not os.path.exists(report_path) or os.path.getsize(report_path) == 0:
        logger.error(f"Report generation failed or produced empty file: {report_path}")
        raise HTTPException(status_code=500, detail="Report generation failed")

    logger.info(f"Report generated successfully: {report_path} (format={format})")
    return FileResponse(
        path=report_path,
        filename=report_filename,
        media_type=media_type,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document and its associated data."""
    doc_data = db.get_document(document_id)
    if not doc_data or doc_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Remove file from disk
    local_path = doc_data.get("path")
    if local_path and os.path.exists(local_path):
        try:
            os.remove(local_path)
        except:
            pass
            
    # Remove local report files from disk
    try:
        report_dir = os.path.join(settings.UPLOAD_DIR, "reports")
        if os.path.exists(report_dir):
            for filename in os.listdir(report_dir):
                if f"LexGuard_Analysis_{document_id}" in filename:
                    try:
                        os.remove(os.path.join(report_dir, filename))
                    except Exception as report_err:
                        logger.error(f"Failed to delete report file: {report_err}")
    except Exception as e:
        logger.error(f"Failed to scan report directory for deletion: {e}")
        
    # Remove file from Supabase Storage
    try:
        from app.services.document_service import get_supabase
        supabase = get_supabase()
        file_ext = doc_data.get("type", "pdf")
        remote_path = f"users/{current_user.id}/documents/{document_id}.{file_ext}"
        supabase.storage.from_("legal-documents").remove([remote_path])
        logger.info(f"Successfully deleted remote document from Supabase: {remote_path}")
    except Exception as e:
        logger.error(f"Failed to delete document from Supabase Storage: {e}")
    
    db.delete_document(document_id)
    db.delete_analysis(document_id)
    db.delete_document_clauses(document_id)
    
    # Delete vector DB index if any
    try:
        from app.services.vector_service import vector_service
        vector_service.delete_index(document_id)
    except:
        pass
        
    return {"success": True, "message": "Document deleted successfully"}
