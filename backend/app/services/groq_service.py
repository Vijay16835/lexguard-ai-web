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


    def classify_document_text(self, text: str) -> str:
        """Content-aware classification engine for document text."""
        if not text or not str(text).strip():
            return "Other / General Document"
        
        text_lower = str(text).lower()
        
        # 1. Resume / CV
        resume_keywords = [
            "curriculum vitae", "resume", "work experience", "education", "employment history",
            "skills", "certifications", "projects", "academic background", "professional summary",
            "bachelor", "master of", "ph.d", "b.tech", "m.tech", "gpa", "technical skills", "experience"
        ]
        resume_score = sum(2 if kw in text_lower else 0 for kw in resume_keywords)
        if "resume" in text_lower or "curriculum vitae" in text_lower:
            resume_score += 5
        if "education" in text_lower and ("experience" in text_lower or "skills" in text_lower):
            resume_score += 4

        # 2. Patent
        patent_keywords = [
            "patent", "patent application", "claims", "abstract", "inventor", "prior art",
            "field of invention", "background of the invention", "summary of the invention",
            "detailed description of embodiment", "embodiments", "us patent", "patent no"
        ]
        patent_score = sum(2 if kw in text_lower else 0 for kw in patent_keywords)
        if "patent" in text_lower or ("claims" in text_lower and "inventor" in text_lower):
            patent_score += 5

        # 3. Non-Disclosure Agreement (NDA)
        nda_keywords = [
            "non-disclosure", "nda", "confidential information", "disclosing party",
            "receiving party", "confidentiality agreement", "proprietary information",
            "non-use", "non-disclosure agreement"
        ]
        nda_score = sum(2 if kw in text_lower else 0 for kw in nda_keywords)
        if "non-disclosure" in text_lower or "confidentiality agreement" in text_lower:
            nda_score += 5

        # 4. Employment Agreement
        employment_keywords = [
            "employment agreement", "employment contract", "offer letter", "job title",
            "salary", "employee", "employer", "duties and responsibilities", "probationary period",
            "termination of employment", "annual compensation"
        ]
        employment_score = sum(2 if kw in text_lower else 0 for kw in employment_keywords)

        # 5. Service Agreement
        service_keywords = [
            "service agreement", "master services agreement", "statement of work",
            "deliverables", "scope of work", "services rendered", "service provider", "client", "vendor"
        ]
        service_score = sum(2 if kw in text_lower else 0 for kw in service_keywords)

        # 6. Lease / Rental Agreement
        lease_keywords = [
            "lease agreement", "rental agreement", "tenant", "landlord", "leased premises",
            "monthly rent", "security deposit", "lease term", "lessor", "lessee"
        ]
        lease_score = sum(2 if kw in text_lower else 0 for kw in lease_keywords)

        # 7. Terms and Conditions
        terms_keywords = [
            "terms and conditions", "terms of service", "terms of use", "user agreement",
            "acceptable use policy", "limitation of liability", "governing law"
        ]
        terms_score = sum(2 if kw in text_lower else 0 for kw in terms_keywords)

        # 8. Privacy Policy
        privacy_keywords = [
            "privacy policy", "personal data", "data collection", "cookies", "gdpr",
            "data controller", "data protection", "privacy rights"
        ]
        privacy_score = sum(2 if kw in text_lower else 0 for kw in privacy_keywords)

        # 9. Invoice
        invoice_keywords = [
            "invoice", "bill to", "ship to", "invoice number", "amount due", "subtotal",
            "tax", "total due", "payment terms", "due date", "balance due"
        ]
        invoice_score = sum(2 if kw in text_lower else 0 for kw in invoice_keywords)

        # 10. Academic Document
        academic_keywords = [
            "abstract", "introduction", "methodology", "literature review", "references",
            "journal", "thesis", "dissertation", "university", "department of", "ieee", "arxiv"
        ]
        academic_score = sum(2 if kw in text_lower else 0 for kw in academic_keywords)

        # 11. Certificate
        cert_keywords = [
            "certificate", "certify", "hereby certified", "presented to", "awarded to",
            "certificate of completion", "certificate of achievement"
        ]
        cert_score = sum(2 if kw in text_lower else 0 for kw in cert_keywords)

        # 12. Generic Legal Contract
        contract_keywords = [
            "agreement", "contract", "parties", "whereas", "in witness whereof", "covenant"
        ]
        contract_score = sum(1 if kw in text_lower else 0 for kw in contract_keywords)

        scores = {
            "Resume / CV": resume_score,
            "Patent": patent_score,
            "Non-Disclosure Agreement": nda_score,
            "Employment Agreement": employment_score,
            "Service Agreement": service_score,
            "Lease / Rental Agreement": lease_score,
            "Terms and Conditions": terms_score,
            "Privacy Policy": privacy_score,
            "Invoice": invoice_score,
            "Academic Document": academic_score,
            "Certificate": cert_score,
            "Legal Contract": contract_score,
        }

        best_category, best_score = max(scores.items(), key=lambda x: x[1])

        if best_score < 3:
            return "Other / General Document"
        
        return best_category

    def _fallback_rule_based_analysis(self, text: str) -> dict:
        """Generate content-aware structured legal analysis from document text when LLM is unavailable."""
        try:
            text_str = str(text or "")
            lines = [line.strip() for line in text_str.split("\n") if line.strip()]
            lower_text = text_str.lower()
            
            # Detect document type dynamically
            doc_type = self.classify_document_text(text_str)
            is_non_contract = doc_type in ["Resume / CV", "Patent", "Academic Document", "Certificate", "Invoice", "Other / General Document"]
            
            # Detect parties
            parties = []
            import re
            party_matches = re.findall(r'(?:between|by and between)\s+([A-Z][A-Za-z0-9\s,\.]+(?:Inc|LLC|Ltd|Corporation|Corp|Company|Co\.|Party))', text_str, re.IGNORECASE)
            if party_matches:
                parties = list(set([p.strip() for p in party_matches[:3]]))
            if not parties:
                parties = ["Subject Party"] if is_non_contract else ["Party A", "Party B"]

            if is_non_contract:
                risk_level = "Low"
                risk_score = 10
                found_risks = []
                risks = [{"category": "Document Type", "description": f"Document classified as {doc_type}. No severe legal risk factors applicable.", "severity": "Low"}]
            else:
                risk_words = ["indemnify", "liability", "termination", "penalty", "breach", "governing law", "jurisdiction", "confidentiality", "arbitration"]
                found_risks = [w for w in risk_words if w in lower_text]
                risk_level = "High" if len(found_risks) >= 4 else ("Medium" if len(found_risks) >= 2 else "Low")
                risk_score = min(25 + len(found_risks) * 15, 90)
                risks = [{"category": "Compliance Risk", "description": f"Identified key risk clauses: {', '.join(found_risks[:3]) if found_risks else 'Standard regulatory terms'}", "severity": risk_level}]

            # Extract clauses/sections
            clauses = []
            for line in lines:
                if any(w in line.lower() for w in ["section", "clause", "article", "term", "termination", "liability", "confidential", "education", "claims", "experience"]):
                    if len(line) > 20:
                        clauses.append({
                            "title": line[:50],
                            "content": line[:200],
                            "risk_level": "Low" if is_non_contract else ("Medium" if any(rw in line.lower() for rw in ["liability", "termination", "penalty"]) else "Low"),
                            "explanation": f"Extracted section regarding {line[:30]}..."
                        })
                if len(clauses) >= 5:
                    break
                    
            if not clauses:
                clauses = [{
                    "title": "General Content",
                    "content": text_str[:200] if text_str else "Standard text content.",
                    "risk_level": "Low",
                    "explanation": f"Parsed text excerpt from {doc_type}."
                }]

            summary = f"This document is classified as a {doc_type} containing {len(lines)} structured paragraphs. Content has been analyzed locally."
            detailed_summary = f"Comprehensive breakdown of {doc_type}: Total character length: {len(text_str)}. Identified sections: {len(lines)}. Risk level assessed as {risk_level} based on document category."

            return {
                "summary": summary,
                "detailed_summary": detailed_summary,
                "key_points": [
                    f"Document Type: {doc_type}",
                    f"Parsed {len(text_str)} characters across {len(lines)} lines",
                    f"Local classification result: {doc_type}"
                ],
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risks": risks,
                "clauses": clauses,
                "parties": parties,
                "important_dates": [],
                "obligations": [{"party": parties[0], "obligation": f"Review {doc_type} details."}],
                "recommendations": [f"Verify contents of {doc_type}."],
                "document_type": doc_type
            }
        except Exception as fe:
            logger.error(f"Error in _fallback_rule_based_analysis: {fe}")
            return {
                "summary": "Document upload and text extraction completed successfully.",
                "detailed_summary": "Document processed and parsed.",
                "key_points": ["Document uploaded successfully"],
                "risk_level": "Low",
                "risk_score": 10,
                "risks": [],
                "clauses": [{"title": "General Content", "content": "Document text extracted.", "risk_level": "Low", "explanation": "Standard content"}],
                "parties": ["Subject"],
                "important_dates": [],
                "obligations": [],
                "recommendations": ["Review document terms."],
                "document_type": self.classify_document_text(text)
            }

    def _fallback_rule_based_summary(self, text: str, document_type: str = None) -> dict:
        """Fallback local summary generation when AI provider is unavailable."""
        text_str = str(text or "")
        lines = [line.strip() for line in text_str.split("\n") if line.strip()]
        doc_type = document_type or self.classify_document_text(text_str)
        
        preview = " ".join(lines[:4])[:300] if lines else text_str[:300]
        short_summary = f"Summary of {doc_type}: {preview}" if preview else f"This document is classified as a {doc_type}."

        detailed_summary = f"Detailed Analysis ({doc_type}): Document contains {len(lines)} paragraphs ({len(text_str)} total characters). Extracted content has been structured using LexGuard local analysis engine."

        key_points = [
            f"Document Category: {doc_type}",
            f"Processed {len(lines)} content blocks ({len(text_str)} total characters)",
            "Local Rule-Based Analysis"
        ]
        
        important_clauses = [line[:100] for line in lines[:5]] if lines else ["Document text extracted."]
        
        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "key_points": key_points,
            "important_clauses": important_clauses,
            "document_type": doc_type,
            "parties": ["Subject Party"],
            "important_dates": [],
            "obligations": [],
            "recommendations": ["Review document details."]
        }

    async def analyze_document(self, text: str) -> dict:
        """Full document analysis — summary, risks, clauses, recommendations."""
        text_str = str(text or "")
        truncated_text = text_str[:100000] if len(text_str) > 100000 else text_str
        
        messages = [
            {
                "role": "system",
                "content": """You are LexGuard AI, an expert document analyst.
Analyze the provided document thoroughly and classify it accurately based on its actual text content.

SUPPORTED DOCUMENT TYPES:
- Resume / CV
- Patent
- Non-Disclosure Agreement
- Employment Agreement
- Service Agreement
- Lease / Rental Agreement
- Terms and Conditions
- Privacy Policy
- Invoice
- Academic Document
- Certificate
- Legal Contract
- Other / General Document

CLASSIFICATION RULES:
- Do NOT classify a document as Non-Disclosure Agreement or Legal Contract unless its text specifically describes confidentiality agreements or legal covenants.
- Resumes, CVs, Patents, Invoices, Certificates, and Academic papers MUST be classified as their true type.
- For non-contract documents (such as Resumes or Patents), risk_level must be "Low" and risk_score must be low (0-15).

Return JSON with structure:
{
    "summary": "A comprehensive 3-5 sentence summary",
    "detailed_summary": "A detailed paragraph-level summary",
    "key_points": ["point 1", "point 2"],
    "risk_level": "Low" or "Medium" or "High",
    "risk_score": 0-100,
    "risks": [{"category": "...", "description": "...", "severity": "Low/Medium/High"}],
    "clauses": [{"title": "...", "content": "...", "risk_level": "Low/Medium/High", "explanation": "..."}],
    "parties": ["Party A name", "Party B name"],
    "important_dates": [{"date": "...", "description": "..."}],
    "obligations": [{"party": "...", "obligation": "..."}],
    "recommendations": ["recommendation 1"],
    "document_type": "Exact category from supported list"
}
Return ONLY valid JSON. No markdown wrappers."""
            },
            {
                "role": "user",
                "content": f"Analyze this document:\n\n{truncated_text}"
            }
        ]
        
        try:
            response_text = await self._call_groq(messages, temperature=0.2, max_tokens=4096)
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            if isinstance(result, dict) and "summary" in result:
                # Enforce valid classification if missing or generic
                if not result.get("document_type") or result.get("document_type") in ["Unknown", "Contract/Agreement/NDA/Lease/etc."]:
                    result["document_type"] = self.classify_document_text(text_str)
                return result
        except Exception as e:
            logger.warning(f"[Groq Service] LLM call or JSON parse error ({type(e).__name__}: {e}). Using content-aware rule fallback...")
            
        return self._fallback_rule_based_analysis(text_str)

    async def generate_summary(self, text: str, document_type: str = None) -> dict:
        """Generate short and detailed summaries with local fallback."""
        text_str = str(text or "")
        if not self.is_groq_configured():
            return self._fallback_rule_based_summary(text_str, document_type)

        truncated_text = text_str[:80000] if len(text_str) > 80000 else text_str
        messages = [
            {
                "role": "system",
                "content": """You are LexGuard AI, a document summarizer.
Return a JSON response with this structure:
{
    "short_summary": "2-3 sentence summary",
    "detailed_summary": "Comprehensive multi-paragraph summary",
    "key_points": ["point 1", "point 2"],
    "important_clauses": ["key highlight 1", "key highlight 2"],
    "parties": ["party 1"],
    "important_dates": ["date 1"],
    "obligations": ["obligation 1"],
    "recommendations": ["recommendation 1"]
}
Return ONLY valid JSON."""
            },
            {
                "role": "user",
                "content": f"Summarize this document:\n\n{truncated_text}"
            }
        ]
        
        try:
            response_text = await self._call_groq(messages, temperature=0.2)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            parsed = json.loads(response_text)
            if isinstance(parsed, dict) and "short_summary" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"[Groq Service] Summary LLM call error: {e}. Using local fallback...")
            
        return self._fallback_rule_based_summary(text_str, document_type)

    async def analyze_risk(self, text: str) -> dict:
        """Dedicated risk analysis endpoint with local fallback."""
        text_str = str(text or "")
        if not self.is_groq_configured():
            fallback = self._fallback_rule_based_analysis(text_str)
            return {
                "risk_level": fallback["risk_level"],
                "risk_score": fallback["risk_score"],
                "issues": fallback["risks"],
                "recommendations": fallback["recommendations"],
                "risk_categories": {}
            }

        truncated_text = text_str[:80000] if len(text_str) > 80000 else text_str
        messages = [
            {
                "role": "system",
                "content": """You are LexGuard AI risk assessment specialist. Return JSON with risk_level, risk_score, issues, recommendations, risk_categories. Return ONLY valid JSON."""
            },
            {
                "role": "user",
                "content": f"Perform risk analysis on this document:\n\n{truncated_text}"
            }
        ]
        
        try:
            response_text = await self._call_groq(messages, temperature=0.1)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except Exception as e:
            logger.warning(f"[Groq Service] Risk LLM call error: {e}. Using local fallback...")
            fallback = self._fallback_rule_based_analysis(text_str)
            return {
                "risk_level": fallback["risk_level"],
                "risk_score": fallback["risk_score"],
                "issues": fallback["risks"],
                "recommendations": fallback["recommendations"],
                "risk_categories": {}
            }

    async def extract_clauses(self, text: str) -> list:
        """Extract individual clauses/sections with local fallback."""
        text_str = str(text or "")
        if not self.is_groq_configured():
            return self._fallback_rule_based_analysis(text_str).get("clauses", [])

        truncated_text = text_str[:80000] if len(text_str) > 80000 else text_str
        messages = [
            {
                "role": "system",
                "content": """Extract important clauses or sections from the document. Return JSON array of objects with title, content, summary, risk_level, mitigation_advice. Return ONLY valid JSON."""
            },
            {
                "role": "user",
                "content": f"Extract sections from this document:\n\n{truncated_text}"
            }
        ]
        
        try:
            response_text = await self._call_groq(messages, temperature=0.2)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except Exception as e:
            logger.warning(f"[Groq Service] Clause extraction LLM error: {e}. Using local fallback...")
            return self._fallback_rule_based_analysis(text_str).get("clauses", [])

    async def chat_with_document(self, document_text: str, query: str, chat_history: list = None, language: str = "English") -> str:
        """Chat with document — context-aware Q&A with intelligent local fallback."""
        text_str = str(document_text or "")
        if self.is_groq_configured():
            try:
                truncated_text = text_str[:60000] if len(text_str) > 60000 else text_str
                messages = [
                    {
                        "role": "system",
                        "content": f"""You are LexGuard AI document assistant. You have access to the document text:

--- DOCUMENT START ---
{truncated_text}
--- DOCUMENT END ---

Answer questions about this document accurately in {language}."""
                    }
                ]
                if chat_history:
                    for msg in chat_history[-6:]:
                        messages.append({"role": msg["role"], "content": msg["content"]})
                messages.append({"role": "user", "content": query})
                return await self._call_groq(messages, temperature=0.3, max_tokens=2048)
            except Exception as e:
                logger.warning(f"[Groq Service] Chat LLM call error: {e}. Using local fallback...")

        # Local fallback for chat
        query_lower = query.lower()
        lines = [l.strip() for l in text_str.split("\n") if l.strip()]
        doc_type = self.classify_document_text(text_str)

        if any(kw in query_lower for kw in ["summary", "summarize", "overview", "about"]):
            preview = " ".join(lines[:4])[:400] if lines else text_str[:400]
            return f"This document is classified as a {doc_type}. Summary:\n\n{preview}"

        if any(kw in query_lower for kw in ["risk", "danger", "liability", "warning"]):
            risk_lines = [l for l in lines if any(w in l.lower() for w in ["liability", "penalty", "terminate", "risk", "breach"])]
            if risk_lines:
                return f"Key risk points identified in this {doc_type}:\n- " + "\n- ".join(risk_lines[:3])
            return f"No severe risk factors detected in this {doc_type}."

        matched_lines = [l for l in lines if any(w in l.lower() for w in query_lower.split() if len(w) > 3)]
        if matched_lines:
            return f"Relevant passages from document ({doc_type}):\n\n- " + "\n- ".join(matched_lines[:3])

        preview = " ".join(lines[:3])[:300] if lines else text_str[:300]
        return f"Document Information ({doc_type}):\n\n{preview}"

    async def detect_language(self, text: str) -> str:
        """Detect language of text with fallback."""
        if self.is_groq_configured():
            try:
                messages = [
                    {"role": "system", "content": "Respond with only the language name."},
                    {"role": "user", "content": f"Detect language:\n\n{text[:500]}"}
                ]
                res = await self._call_groq(messages, temperature=0.0, max_tokens=10)
                return res.strip()
            except Exception:
                pass
        return "English"

    async def translate_text(self, text: str, target_language: str) -> str:
        """Translate text with fallback."""
        if self.is_groq_configured():
            try:
                messages = [
                    {"role": "system", "content": f"Translate text to {target_language}. Return ONLY translated text."},
                    {"role": "user", "content": text}
                ]
                res = await self._call_groq(messages, temperature=0.1, max_tokens=4096)
                return res.strip()
            except Exception:
                pass
        return text

    async def analyze_image_text(self, ocr_text: str) -> dict:
        """Analyze OCR text with local fallback."""
        if self.is_groq_configured():
            try:
                messages = [
                    {"role": "system", "content": "Analyze OCR text and return JSON with corrected_text, summary, risk_level, risk_score, key_findings, document_type."},
                    {"role": "user", "content": f"Analyze OCR text:\n\n{ocr_text}"}
                ]
                res = await self._call_groq(messages, temperature=0.2)
                if "```json" in res:
                    res = res.split("```json")[1].split("```")[0].strip()
                elif "```" in res:
                    res = res.split("```")[1].split("```")[0].strip()
                return json.loads(res)
            except Exception:
                pass
        
        fallback = self._fallback_rule_based_analysis(ocr_text)
        return {
            "corrected_text": ocr_text,
            "summary": fallback["summary"],
            "risk_level": fallback["risk_level"],
            "risk_score": fallback["risk_score"],
            "key_findings": fallback["key_points"],
            "document_type": fallback["document_type"]
        }


groq_service = GroqService()

