"""
Groq AI Service for LexGuard AI
Handles all AI-powered legal document analysis via Groq API.
Uses llama-3.3-70b-versatile for high-quality legal reasoning.
"""
import json
import httpx
import traceback
from app.core.config import settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _call_groq(self, messages: list, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        """Make a request to Groq API and return the response text."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    GROQ_API_URL,
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            print(f"Groq API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Groq API error: {e.response.status_code}")
        except Exception as e:
            print(f"Groq API call failed: {e}")
            traceback.print_exc()
            raise

    async def analyze_document(self, text: str) -> dict:
        """Full legal document analysis — summary, risks, clauses, recommendations."""
        # Truncate to fit context window (roughly 120k chars for 70b model)
        truncated_text = text[:100000] if len(text) > 100000 else text
        
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
        
        response_text = await self._call_groq(messages, temperature=0.2, max_tokens=4096)
        
        # Parse JSON from response
        try:
            # Try to extract JSON if wrapped in code fences
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            print(f"Failed to parse Groq response as JSON: {response_text[:500]}")
            return {
                "summary": response_text[:500],
                "detailed_summary": response_text,
                "key_points": [],
                "risk_level": "Medium",
                "risk_score": 50,
                "risks": [],
                "clauses": [],
                "parties": [],
                "important_dates": [],
                "obligations": [],
                "recommendations": ["Unable to parse structured analysis. Please review the summary."],
                "document_type": "Unknown"
            }

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
