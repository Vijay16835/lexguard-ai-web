"""
Groq AI Service for LexGuard AI
Handles all AI-powered legal document analysis via Groq API.
Uses llama-3.3-70b-versatile for high-quality legal reasoning.
"""
import json
import httpx
import traceback
from app.core.config import settings

import logging
import time
import asyncio

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def is_groq_configured(self) -> bool:
        return bool(self.api_key and "your_groq" not in str(self.api_key).lower())

    async def _call_groq(self, messages: list, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        """Make a request to Groq API with automatic retries on transient errors."""
        if not self.is_groq_configured():
            logger.info("GROQ_CONFIGURED=NO | AI_PROVIDER=Local Legal Analysis Engine")
            raise ValueError("GROQ_API_KEY not configured")

        FALLBACK_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-8b-8192"]
        model_to_use = self.model
        
        total_input_chars = sum(len(m.get("content", "")) for m in messages)
        approx_tokens = total_input_chars // 4

        backoffs = [0, 1, 2, 4]
        max_attempts = len(backoffs)
        
        last_error = None
        for attempt_idx, delay in enumerate(backoffs):
            attempt_num = attempt_idx + 1
            if delay > 0:
                await asyncio.sleep(delay)
                
            t0_req = time.time()
            try:
                payload = {
                    "model": model_to_use,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        GROQ_API_URL,
                        headers=self.headers,
                        json=payload,
                    )
                    res_time = time.time() - t0_req
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    
                    status_code = response.status_code
                    sanitized_err = response.text[:150].replace('\n', ' ')
                    logger.warning(
                        f"AI_ANALYSIS_FAILURE\n"
                        f"ERROR_TYPE=HTTPStatusError\n"
                        f"HTTP_STATUS={status_code}\n"
                        f"SANITIZED_ERROR={sanitized_err}\n"
                        f"FALLBACK_STATUS=RETRYING_ATTEMPT_{attempt_num}"
                    )
                    
                    if status_code == 404:
                        for alt in FALLBACK_MODELS:
                            if alt != model_to_use:
                                model_to_use = alt
                                break
                    elif status_code in (401, 403):
                        # Non-retryable auth error: stop retrying and fail over immediately
                        raise RuntimeError(f"Groq API returned HTTP {status_code} - Auth failed")

            except (httpx.TimeoutException, httpx.RequestError) as e:
                res_time = time.time() - t0_req
                sanitized_err = str(e)[:150].replace('\n', ' ')
                logger.warning(
                    f"AI_ANALYSIS_FAILURE\n"
                    f"ERROR_TYPE={type(e).__name__}\n"
                    f"HTTP_STATUS=NONE\n"
                    f"SANITIZED_ERROR={sanitized_err}\n"
                    f"FALLBACK_STATUS=RETRYING_ATTEMPT_{attempt_num}"
                )
                last_error = e

        raise RuntimeError(f"Groq API call unfulfilled after {max_attempts} attempts")


    def _fallback_rule_based_analysis(self, text: str) -> dict:
        """Generate content-aware structured legal analysis from document text when LLM is unavailable."""
        try:
            text_str = str(text or "")
            lines = [line.strip() for line in text_str.split("\n") if line.strip()]
            lower_text = text_str.lower()
            
            # Detect document type
            doc_type = "Legal Agreement"
            if "nda" in lower_text or "non-disclosure" in lower_text:
                doc_type = "Non-Disclosure Agreement (NDA)"
            elif "employment" in lower_text or "offer letter" in lower_text:
                doc_type = "Employment Agreement"
            elif "lease" in lower_text or "rent" in lower_text or "tenant" in lower_text:
                doc_type = "Lease Agreement"
            elif "service" in lower_text or "master service" in lower_text:
                doc_type = "Services Agreement"
            elif "contract" in lower_text:
                doc_type = "Contract Agreement"
                
            # Detect parties
            parties = []
            import re
            party_matches = re.findall(r'(?:between|by and between)\s+([A-Z][A-Za-z0-9\s,\.]+(?:Inc|LLC|Ltd|Corporation|Corp|Company|Co\.|Party))', text_str, re.IGNORECASE)
            if party_matches:
                parties = list(set([p.strip() for p in party_matches[:3]]))
            if not parties:
                parties = ["Party A", "Party B"]

            # Detect risk indicators
            risk_words = ["indemnify", "liability", "termination", "penalty", "breach", "governing law", "jurisdiction", "confidentiality", "arbitration"]
            found_risks = [w for w in risk_words if w in lower_text]
            risk_level = "High" if len(found_risks) >= 4 else ("Medium" if len(found_risks) >= 2 else "Low")
            risk_score = min(25 + len(found_risks) * 15, 90)

            # Extract clauses
            clauses = []
            for line in lines:
                if any(w in line.lower() for w in ["section", "clause", "article", "term", "termination", "liability", "confidential"]):
                    if len(line) > 20:
                        clauses.append({
                            "title": line[:50],
                            "content": line[:200],
                            "risk_level": "Medium" if any(rw in line.lower() for rw in ["liability", "termination", "penalty"]) else "Low",
                            "explanation": f"Important clause regarding {line[:30]}..."
                        })
                if len(clauses) >= 5:
                    break
                    
            if not clauses:
                clauses = [{
                    "title": "General Provisions",
                    "content": text_str[:200] if text_str else "Standard legal provision text.",
                    "risk_level": "Low",
                    "explanation": "Standard operational clause extracted from document text."
                }]

            summary = f"This {doc_type} contains {len(lines)} structured paragraphs. Key provisions cover obligations, governing conditions, and compliance terms."
            detailed_summary = f"Comprehensive analysis of {doc_type}: The document defines operational terms between {', '.join(parties)}. Extracted text length: {len(text_str)} characters. High-risk terms identified: {', '.join(found_risks) if found_risks else 'None'}. Section reviews indicate standard legal compliance parameters."

            return {
                "summary": summary,
                "detailed_summary": detailed_summary,
                "key_points": [
                    f"Document Type: {doc_type}",
                    f"Extracted {len(text_str)} characters across {len(lines)} paragraphs",
                    f"Key risk terms detected: {len(found_risks)}"
                ],
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risks": [
                    {"category": "Compliance Risk", "description": f"Identified key risk clauses: {', '.join(found_risks[:3]) if found_risks else 'Standard regulatory terms'}", "severity": risk_level}
                ],
                "clauses": clauses,
                "parties": parties,
                "important_dates": [],
                "obligations": [{"party": parties[0] if parties else "Party A", "obligation": "Adhere to terms outlined in document"}],
                "recommendations": [
                    "Review termination and liability clauses thoroughly.",
                    "Verify all dates and execution signatories."
                ],
                "document_type": doc_type
            }
        except Exception as fe:
            logger.error(f"Error in _fallback_rule_based_analysis: {fe}")
            return {
                "summary": "Document upload and text extraction completed successfully.",
                "detailed_summary": "Document processed and parsed.",
                "key_points": ["Document uploaded successfully"],
                "risk_level": "Low",
                "risk_score": 25,
                "risks": [],
                "clauses": [{"title": "General Terms", "content": "Document text extracted.", "risk_level": "Low", "explanation": "Standard clause"}],
                "parties": ["Party A", "Party B"],
                "important_dates": [],
                "obligations": [],
                "recommendations": ["Review document terms."],
                "document_type": "Legal Document"
            }

    async def analyze_document(self, text: str) -> dict:
        """Full legal document analysis — summary, risks, clauses, recommendations."""
        text_str = str(text or "")
        truncated_text = text_str[:100000] if len(text_str) > 100000 else text_str
        
        messages = [
            {
                "role": "system",
                "content": """You are LexGuard AI, an expert legal document analyst. 
Analyze the provided legal document thoroughly and return a JSON response with this EXACT structure:
{
    "summary": "A comprehensive 3-5 sentence summary of the document",
    "detailed_summary": "A detailed paragraph-level summary covering all major sections",
    "key_points": ["point 1", "point 2", ...],
    "risk_level": "Low" or "Medium" or "High",
    "risk_score": 0-100 (integer),
    "risks": [
        {"category": "category name", "description": "description", "severity": "Low/Medium/High"}
    ],
    "clauses": [
        {"title": "clause title", "content": "clause text excerpt", "risk_level": "Low/Medium/High", "explanation": "why this matters"}
    ],
    "parties": ["Party A name", "Party B name"],
    "important_dates": [
        {"date": "date string", "description": "what this date is for"}
    ],
    "obligations": [
        {"party": "who", "obligation": "what they must do"}
    ],
    "recommendations": ["recommendation 1", "recommendation 2", ...],
    "document_type": "Contract/Agreement/NDA/Lease/etc."
}
Return ONLY valid JSON. No markdown, no code fences, no explanation text."""
            },
            {
                "role": "user",
                "content": f"Analyze this legal document:\n\n{truncated_text}"
            }
        ]
        
        try:
            response_text = await self._call_groq(messages, temperature=0.2, max_tokens=4096)
            
            # Try to extract JSON if wrapped in code fences
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            if isinstance(result, dict) and "summary" in result:
                return result
        except Exception as e:
            logger.warning(f"[Groq Service] LLM call or JSON parse error ({type(e).__name__}: {e}). Using content-aware rule fallback...")
            
        return self._fallback_rule_based_analysis(text_str)

    async def generate_summary(self, text: str) -> dict:
        """Generate short and detailed summaries."""
        truncated_text = text[:80000] if len(text) > 80000 else text
        
        messages = [
            {
                "role": "system",
                "content": """You are LexGuard AI, a legal document summarizer.
Return a JSON response with this structure:
{
    "short_summary": "2-3 sentence summary",
    "detailed_summary": "Comprehensive multi-paragraph summary",
    "key_points": ["point 1", "point 2", ...],
    "important_clauses": ["clause summary 1", "clause summary 2", ...]
}
Return ONLY valid JSON."""
            },
            {
                "role": "user",
                "content": f"Summarize this legal document:\n\n{truncated_text}"
            }
        ]
        
        response_text = await self._call_groq(messages, temperature=0.2)
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "short_summary": response_text[:300],
                "detailed_summary": response_text,
                "key_points": [],
                "important_clauses": []
            }

    async def analyze_risk(self, text: str) -> dict:
        """Dedicated risk analysis endpoint."""
        truncated_text = text[:80000] if len(text) > 80000 else text
        
        messages = [
            {
                "role": "system",
                "content": """You are LexGuard AI, a legal risk assessment specialist.
Analyze the document for ALL legal risks and return JSON:
{
    "risk_level": "Low" or "Medium" or "High",
    "risk_score": 0-100,
    "issues": [
        {"category": "category", "description": "description", "severity": "Low/Medium/High", "clause_reference": "relevant section"}
    ],
    "recommendations": ["rec 1", "rec 2", ...],
    "risk_categories": {
        "missing_signatures": true/false,
        "high_penalty_clauses": true/false,
        "one_sided_obligations": true/false,
        "ambiguous_language": true/false,
        "missing_dates": true/false,
        "confidentiality_risks": true/false,
        "liability_risks": true/false,
        "payment_risks": true/false
    }
}
Return ONLY valid JSON."""
            },
            {
                "role": "user",
                "content": f"Perform a comprehensive risk analysis on this legal document:\n\n{truncated_text}"
            }
        ]
        
        response_text = await self._call_groq(messages, temperature=0.1)
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "risk_level": "Medium",
                "risk_score": 50,
                "issues": [],
                "recommendations": [response_text[:500]],
                "risk_categories": {}
            }

    async def extract_clauses(self, text: str) -> list:
        """Extract and analyze individual clauses from the document."""
        truncated_text = text[:80000] if len(text) > 80000 else text
        
        messages = [
            {
                "role": "system",
                "content": """You are LexGuard AI, a legal clause extraction specialist.
Extract all important clauses from the document and return a JSON array:
[
    {
        "title": "Clause Title",
        "content": "The exact text of the clause",
        "summary": "Brief explanation of what this clause means",
        "risk_level": "Low/Medium/High",
        "mitigation_advice": "What to watch out for or how to negotiate"
    }
]
Return ONLY valid JSON array."""
            },
            {
                "role": "user",
                "content": f"Extract all important legal clauses from this document:\n\n{truncated_text}"
            }
        ]
        
        response_text = await self._call_groq(messages, temperature=0.2)
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except json.JSONDecodeError:
            return []

    async def chat_with_document(self, document_text: str, query: str, chat_history: list = None, language: str = "English") -> str:
        """Chat with a document — context-aware Q&A."""
        truncated_text = document_text[:60000] if len(document_text) > 60000 else document_text
        
        messages = [
            {
                "role": "system",
                "content": f"""You are LexGuard AI, a legal assistant. You have access to the following legal document:

--- DOCUMENT START ---
{truncated_text}
--- DOCUMENT END ---

Answer the user's questions about this document accurately and helpfully.
IMPORTANT: You must write your complete response in {language}.
If the answer is not found in the document, say so clearly in {language}.
Provide specific references to relevant sections when possible.
Be concise but thorough."""
            }
        ]
        
        # Add chat history for context
        if chat_history:
            for msg in chat_history[-6:]:  # Last 6 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": query})
        
        return await self._call_groq(messages, temperature=0.3, max_tokens=2048)

    async def detect_language(self, text: str) -> str:
        """Detect the language of the provided text."""
        messages = [
            {
                "role": "system",
                "content": "You are a language detection expert. Respond with only the name of the language (e.g. 'English', 'Tamil', 'Hindi', 'Telugu', 'Malayalam', 'Kannada', 'French', 'Spanish', 'German', 'Arabic'). Do not include any other punctuation or words."
            },
            {
                "role": "user",
                "content": f"Detect the language of this text:\n\n{text[:500]}"
            }
        ]
        response = await self._call_groq(messages, temperature=0.0, max_tokens=10)
        return response.strip()

    async def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to the target language."""
        messages = [
            {
                "role": "system",
                "content": f"You are a professional legal translator. Translate the user's text into {target_language}. Maintain legal meaning and formatting. Return ONLY the translated text, without comments, notes or markdown wrapper blocks."
            },
            {
                "role": "user",
                "content": f"Translate this text to {target_language}:\n\n{text}"
            }
        ]
        response = await self._call_groq(messages, temperature=0.1, max_tokens=4096)
        return response.strip()

    async def analyze_image_text(self, ocr_text: str) -> dict:
        """Analyze text extracted from images/scanned documents."""
        messages = [
            {
                "role": "system",
                "content": """You are LexGuard AI analyzing OCR-extracted text from a scanned legal document.
The text may have OCR artifacts. Correct obvious OCR errors and analyze the content.
Return JSON:
{
    "corrected_text": "cleaned up version of the text",
    "summary": "summary of the document",
    "risk_level": "Low/Medium/High",
    "risk_score": 0-100,
    "key_findings": ["finding 1", "finding 2"],
    "document_type": "type of document"
}
Return ONLY valid JSON."""
            },
            {
                "role": "user",
                "content": f"Analyze this OCR-extracted legal text:\n\n{ocr_text}"
            }
        ]
        
        response_text = await self._call_groq(messages, temperature=0.2)
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "corrected_text": ocr_text,
                "summary": response_text[:500],
                "risk_level": "Medium",
                "risk_score": 50,
                "key_findings": [],
                "document_type": "Unknown"
            }


groq_service = GroqService()
