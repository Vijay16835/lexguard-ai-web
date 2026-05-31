"""
AI Service Facade for LexGuard AI
Provides a unified interface to all AI capabilities.
Delegates to groq_service, vector_service, and analysis_service.
"""
from app.services.groq_service import groq_service
from app.services.analysis_service import analysis_service


class AIService:
    """High-level facade for all AI operations."""

    def __init__(self):
        self.groq = groq_service
        self.analysis = analysis_service

    async def analyze_document(self, text: str) -> dict:
        """Full document analysis via Groq."""
        return await self.groq.analyze_document(text)

    async def generate_summary(self, text: str) -> dict:
        """Generate document summary via Groq."""
        return await self.groq.generate_summary(text)

    async def analyze_risk(self, text: str) -> dict:
        """Dedicated risk analysis via Groq."""
        return await self.groq.analyze_risk(text)

    async def extract_clauses(self, text: str) -> list:
        """Extract clauses via Groq."""
        return await self.groq.extract_clauses(text)

    async def chat_with_document(self, text: str, query: str, history: list = None) -> str:
        """Chat with a document via Groq."""
        return await self.groq.chat_with_document(text, query, history)

    async def analyze_image_text(self, ocr_text: str) -> dict:
        """Analyze OCR-extracted text via Groq."""
        return await self.groq.analyze_image_text(ocr_text)


ai_service = AIService()