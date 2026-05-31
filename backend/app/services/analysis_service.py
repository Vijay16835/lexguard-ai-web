"""
Analysis Service for LexGuard AI
Provides reusable analysis orchestration logic.
Can be called from API routes or background tasks.
"""
import uuid
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.analysis import Analysis
from app.models.clause import Clause
from app.services.document_service import extract_text, get_file_extension
from app.services.groq_service import groq_service


class AnalysisService:
    """Orchestrates the full document analysis pipeline."""

    async def run_full_analysis(self, db: Session, document_id: str):
        """
        Run or re-run the complete AI analysis pipeline on a document.
        Expects the document to already have extracted_text populated.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        if not doc.extracted_text:
            raise ValueError(f"Document {document_id} has no extracted text")

        # 1. Run Groq analysis
        analysis_result = await groq_service.analyze_document(doc.extracted_text)

        # 2. Update document quick-access fields
        doc.risk_score = analysis_result.get("risk_score", 0)
        doc.risk_level = analysis_result.get("risk_level", "Medium")
        doc.summary = analysis_result.get("summary", "")
        doc.document_type = analysis_result.get("document_type", "Unknown")
        doc.status = "completed"
        doc.analyzed_at = datetime.now(timezone.utc)

        # 3. Upsert Analysis record
        existing = db.query(Analysis).filter(Analysis.document_id == document_id).first()
        if existing:
            db.delete(existing)
            db.flush()

        new_analysis = Analysis(
            document_id=document_id,
            risk_level=analysis_result.get("risk_level", "Medium"),
            risk_score=analysis_result.get("risk_score", 0),
            summary=analysis_result.get("summary", ""),
            ai_confidence=0.85,
            parties=analysis_result.get("parties", []),
            important_dates=analysis_result.get("important_dates", []),
            recommendations=analysis_result.get("recommendations", []),
            raw_analysis_data=analysis_result,
        )
        db.add(new_analysis)

        # 4. Upsert Clauses
        db.query(Clause).filter(Clause.document_id == document_id).delete()
        for clause_data in analysis_result.get("clauses", []):
            clause = Clause(
                document_id=document_id,
                title=clause_data.get("title", "Untitled Clause"),
                content=clause_data.get("content", ""),
                summary=clause_data.get("explanation", clause_data.get("summary", "")),
                risk_level=clause_data.get("risk_level", "Low"),
                mitigation_advice=clause_data.get("mitigation_advice", ""),
            )
            db.add(clause)

        db.commit()
        return analysis_result

    async def run_vector_indexing(self, document_id: str, text: str):
        """Create vector index for a document's text."""
        try:
            from app.services.vector_service import vector_service
            await vector_service.create_vector_index(document_id, text)
        except Exception as e:
            print(f"Vector indexing failed for {document_id}: {e}")


analysis_service = AnalysisService()
