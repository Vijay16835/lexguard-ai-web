from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import re
import logging
import traceback
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.api.deps import get_current_user
from app.services.groq_service import groq_service

router = APIRouter()
logger = logging.getLogger(__name__)

class DetectLanguageRequest(BaseModel):
    text: str

class TranslateRequest(BaseModel):
    text: str
    target_language: str

class MultilingualChatRequest(BaseModel):
    document_id: str
    message: str
    language: str = "English"

def clean_markdown_for_tts(text: str) -> str:
    """Clean markdown markers like asterisks, hashes, and list bullets to make text smooth to read."""
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    text = re.sub(r'^\s*[-*+]\s+', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'\n+', ' . ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

@router.post("/detect-language")
async def detect_language(request: DetectLanguageRequest):
    try:
        lang = await groq_service.detect_language(request.text)
        return {"success": True, "language": lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")

@router.post("/translate")
async def translate_text(request: TranslateRequest):
    try:
        translated = await groq_service.translate_text(request.text, request.target_language)
        return {"success": True, "translated_text": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@router.post("/chat/multilingual")
async def chat_multilingual(
    request: MultilingualChatRequest,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"[MultilingualChat] Entry: document_id='{request.document_id}', user_id='{current_user.id}', language='{request.language}', message='{request.message[:80]}'")

    # 1. Retrieve document from DB
    logger.info(f"[MultilingualChat] Fetching document '{request.document_id}' from database...")
    doc_data = db.get_document(request.document_id)

    if not doc_data:
        logger.error(f"[MultilingualChat] Document '{request.document_id}' not found in any database (PostgreSQL + Firestore).")
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.document_id}' not found. It may have been deleted or the ID is incorrect."
        )

    logger.info(f"[MultilingualChat] Document found: name='{doc_data.get('name')}', status='{doc_data.get('status')}', user_id='{doc_data.get('user_id')}'")

    # 2. Ownership check — compare IDs as strings for safety
    doc_owner_id = str(doc_data.get("user_id", "")).strip()
    current_user_id = str(current_user.id).strip()
    if doc_owner_id != current_user_id:
        logger.warning(
            f"[MultilingualChat] Ownership mismatch: doc.user_id='{doc_owner_id}' vs current_user.id='{current_user_id}'"
        )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to chat with this document."
        )

    # 3. Check for extracted text
    extracted_text = doc_data.get("extracted_text") or doc_data.get("text") or ""
    extracted_text = extracted_text.strip() if extracted_text else ""

    if not extracted_text:
        doc_status = doc_data.get("status", "unknown")
        logger.error(
            f"[MultilingualChat] No extracted_text for document '{request.document_id}'. "
            f"Status='{doc_status}'. Analysis may not be complete."
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Document text is not yet available (status: '{doc_status}'). "
                "Please wait for the analysis to complete before chatting."
            )
        )

    logger.info(f"[MultilingualChat] Extracted text available: {len(extracted_text)} chars. Proceeding with chat.")

    try:
        # 4. Use first 60k chars as context
        context = extracted_text[:60000]

        # 5. Get recent chat history for conversational context
        logger.info(f"[MultilingualChat] Fetching recent chat history for document '{request.document_id}'...")
        try:
            recent_chats = db.get_chat_history(request.document_id, current_user.id)
            recent_chats = recent_chats[-6:]
            logger.info(f"[MultilingualChat] {len(recent_chats)} recent chat entries loaded.")
        except Exception as hist_err:
            logger.warning(f"[MultilingualChat] Failed to load chat history (non-fatal): {hist_err}")
            recent_chats = []

        chat_history = []
        for chat in recent_chats:
            chat_history.append({"role": "user", "content": chat.get("query", "")})
            chat_history.append({"role": "assistant", "content": chat.get("response", "")})

        # 6. Call Groq AI
        logger.info(f"[MultilingualChat] Calling Groq AI (language='{request.language}')...")
        answer = await groq_service.chat_with_document(
            context, request.message, chat_history, language=request.language
        )
        logger.info(f"[MultilingualChat] Groq AI responded: {len(answer)} chars.")

        # 7. Save to chat history (non-fatal if fails)
        try:
            db.save_chat_entry({
                "document_id": request.document_id,
                "user_id": current_user.id,
                "query": request.message,
                "response": answer,
                "language": request.language
            })
            logger.info(f"[MultilingualChat] Chat entry saved to history.")
        except Exception as save_err:
            logger.warning(f"[MultilingualChat] Failed to save chat entry (non-fatal): {save_err}")

        logger.info(f"[MultilingualChat] Success. Returning answer to client.")
        return {
            "success": True,
            "answer": answer,
            "document_id": request.document_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MultilingualChat] Unexpected error: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"AI chat failed: {type(e).__name__}: {str(e)}"
        )

@router.post("/chat/voice")
async def chat_voice(
    request: MultilingualChatRequest,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Voice chat: same as multilingual chat but cleans response for TTS synthesis."""
    logger.info(f"[VoiceChat] Entry: document_id='{request.document_id}', user='{current_user.id}'")
    try:
        response = await chat_multilingual(request, db, current_user)
        clean_answer = clean_markdown_for_tts(response["answer"])
        response["voice_ready_answer"] = clean_answer
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VoiceChat] Unexpected error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {type(e).__name__}: {str(e)}")

@router.get("/summary/audio/{document_id}")
async def summary_audio(
    document_id: str,
    language: str = "English",
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"[SummaryAudio] Entry: document_id='{document_id}', language='{language}', user='{current_user.id}'")
    doc_data = db.get_document(document_id)
    if not doc_data or str(doc_data.get("user_id", "")).strip() != str(current_user.id).strip():
        raise HTTPException(status_code=404, detail="Document not found")

    analysis = db.get_analysis(document_id)
    summary_text = analysis.get("summary") if (analysis and analysis.get("summary")) else doc_data.get("summary")
    if not summary_text:
        raise HTTPException(status_code=404, detail="Summary not generated yet. Analyze the document first.")

    try:
        translated_text = summary_text
        if language.lower() != "english":
            cached = db.get_translated_summary(document_id, language)
            if cached:
                translated_text = cached.get("summary")
            else:
                translated_text = await groq_service.translate_text(summary_text, language)
                db.save_translated_summary(document_id, language, translated_text)

        clean_text = clean_markdown_for_tts(translated_text)
        return {
            "success": True,
            "document_id": document_id,
            "language": language,
            "summary_text": translated_text,
            "audio_clean_text": clean_text
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SummaryAudio] Error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"TTS summary failed: {str(e)}")
