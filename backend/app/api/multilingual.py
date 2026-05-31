from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import re
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.api.deps import get_current_user
from app.services.groq_service import groq_service

router = APIRouter()

class DetectLanguageRequest(BaseModel):
    text: str

class TranslateRequest(BaseModel):
    text: str
    target_language: str

class MultilingualChatRequest(BaseModel):
    document_id: str
    message: str
    language: str

def clean_markdown_for_tts(text: str) -> str:
    """Clean markdown markers like asterisks, hashes, and list bullets to make text smooth to read."""
    # Remove headers
    text = re.sub(r'#+\s*', '', text)
    # Remove bold/italic stars and underscores
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    # Replace list dashes/bullets with simple formatting
    text = re.sub(r'^\s*[-*+]\s+', ' ', text, flags=re.MULTILINE)
    # Replace numbered lists with just the numbers
    text = re.sub(r'^\s*\d+\.\s+', ' ', text, flags=re.MULTILINE)
    # Replace multiple spaces/newlines
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
    doc_data = db.get_document(request.document_id)
    if not doc_data or doc_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    extracted_text = doc_data.get("extracted_text")
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Document text not yet extracted.")

    try:
        # Retrieve context
        context = extracted_text[:60000]
        
        # Chat history
        recent_chats = db.get_chat_history(request.document_id, current_user.id)
        recent_chats = recent_chats[-6:] # Limit to last 6
        
        chat_history = []
        for chat in recent_chats:
            chat_history.append({"role": "user", "content": chat["query"]})
            chat_history.append({"role": "assistant", "content": chat["response"]})

        # Call groq service with language specifier
        answer = await groq_service.chat_with_document(
            context, request.message, chat_history, language=request.language
        )

        # Save to chat history with language in Firestore
        db.save_chat_entry({
            "document_id": request.document_id,
            "user_id": current_user.id,
            "query": request.message,
            "response": answer,
            "language": request.language
        })

        return {
            "success": True,
            "answer": answer,
            "document_id": request.document_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multilingual chat failed: {str(e)}")

@router.post("/chat/voice")
async def chat_voice(
    request: MultilingualChatRequest,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Voice chat: same as multilingual chat but clean response for TTS synthesis."""
    try:
        response = await chat_multilingual(request, db, current_user)
        # Clean answer for speech
        clean_answer = clean_markdown_for_tts(response["answer"])
        response["voice_ready_answer"] = clean_answer
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice chat failed: {str(e)}")

@router.get("/summary/audio/{document_id}")
async def summary_audio(
    document_id: str,
    language: str = "English",
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_data = db.get_document(document_id)
    if not doc_data or doc_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get summary from DB
    analysis = db.get_analysis(document_id)
    summary_text = analysis.get("summary") if (analysis and analysis.get("summary")) else doc_data.get("summary")
    if not summary_text:
        raise HTTPException(status_code=404, detail="Summary not generated yet. Analyze the document first.")

    try:
        translated_text = summary_text
        if language.lower() != "english":
            # Check cache
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS summary translation/cleanup failed: {str(e)}")
