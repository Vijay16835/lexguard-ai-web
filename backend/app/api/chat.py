from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging
import traceback
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.api.deps import get_current_user
from app.services.groq_service import groq_service

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    document_id: str
    message: str


@router.post("/document")
async def chat_with_document(
    request: ChatRequest,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ask a question about a specific document.
    Uses RAG: vector search for context retrieval + Groq for answer generation.
    """
    logger.info(f"[ChatDoc] Entry: document_id='{request.document_id}', user_id='{current_user.id}', message='{request.message[:80]}'")

    # 1. Validate document belongs to user and has extracted text
    logger.info(f"[ChatDoc] Fetching document '{request.document_id}' from database...")
    doc_data = db.get_document(request.document_id)

    if not doc_data:
        logger.error(f"[ChatDoc] Document '{request.document_id}' not found in any database.")
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.document_id}' not found. It may have been deleted or the ID is incorrect."
        )

    logger.info(f"[ChatDoc] Document found: name='{doc_data.get('name')}', status='{doc_data.get('status')}', user_id='{doc_data.get('user_id')}'")

    # Ownership check — compare as strings for safety
    doc_owner_id = str(doc_data.get("user_id", "")).strip()
    current_user_id = str(current_user.id).strip()
    if doc_owner_id != current_user_id:
        logger.warning(f"[ChatDoc] Ownership mismatch: doc.user_id='{doc_owner_id}' vs current_user.id='{current_user_id}'")
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to chat with this document."
        )

    # 2. Check for extracted text (support both field name variants)
    extracted_text = doc_data.get("extracted_text") or doc_data.get("text") or ""
    extracted_text = extracted_text.strip() if extracted_text else ""

    if not extracted_text:
        doc_status = doc_data.get("status", "unknown")
        logger.error(
            f"[ChatDoc] No extracted_text for document '{request.document_id}'. "
            f"Status='{doc_status}'."
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Document text is not yet available (status: '{doc_status}'). "
                "Please wait for the analysis to complete before chatting."
            )
        )

    logger.info(f"[ChatDoc] Extracted text available: {len(extracted_text)} chars.")

    try:
        # 3. Try vector search for relevant context
        context_chunks = []
        try:
            from app.services.vector_service import vector_service
            context_chunks = await vector_service.search_similar_chunks(
                request.document_id, request.message, top_k=4
            )
            logger.info(f"[ChatDoc] Vector search returned {len(context_chunks)} chunks.")
        except Exception as vec_err:
            logger.warning(f"[ChatDoc] Vector search failed, falling back to full text: {vec_err}")

        # 4. Build context
        if context_chunks:
            context = "\n\n---\n\n".join(context_chunks)
        else:
            context = extracted_text[:60000]
        logger.info(f"[ChatDoc] Context built: {len(context)} chars.")

        # 5. Get recent chat history for conversational context
        logger.info(f"[ChatDoc] Fetching recent chat history...")
        try:
            recent_chats = db.get_chat_history(request.document_id, current_user.id)
            recent_chats = recent_chats[-6:]
            logger.info(f"[ChatDoc] Loaded {len(recent_chats)} recent chat entries.")
        except Exception as hist_err:
            logger.warning(f"[ChatDoc] Failed to load chat history (non-fatal): {hist_err}")
            recent_chats = []

        chat_history = []
        for chat in recent_chats:
            chat_history.append({"role": "user", "content": chat.get("query", "")})
            chat_history.append({"role": "assistant", "content": chat.get("response", "")})

        # 6. Call Groq AI
        logger.info(f"[ChatDoc] Calling Groq AI...")
        answer = await groq_service.chat_with_document(
            context, request.message, chat_history
        )
        logger.info(f"[ChatDoc] Groq AI responded: {len(answer)} chars.")

        # 7. Save to chat history (non-fatal if fails)
        try:
            db.save_chat_entry({
                "document_id": request.document_id,
                "user_id": current_user.id,
                "query": request.message,
                "response": answer,
                "language": "English"
            })
            logger.info(f"[ChatDoc] Chat entry saved.")
        except Exception as save_err:
            logger.warning(f"[ChatDoc] Failed to save chat entry (non-fatal): {save_err}")

        logger.info(f"[ChatDoc] Success. Returning answer.")
        return {
            "success": True,
            "answer": answer,
            "document_id": request.document_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ChatDoc] Unexpected error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {type(e).__name__}: {str(e)}")


@router.get("/history/{document_id}")
async def get_chat_history(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve chat history for a document."""
    logger.info(f"[ChatHistory] Fetching history for document='{document_id}', user='{current_user.id}'")
    try:
        chats = db.get_chat_history(document_id, current_user.id)
        logger.info(f"[ChatHistory] Found {len(chats)} entries.")
        return {
            "success": True,
            "history": [
                {
                    "id": h.get("id"),
                    "query": h.get("query"),
                    "response": h.get("response"),
                    "created_at": h.get("created_at"),
                }
                for h in chats
            ]
        }
    except Exception as e:
        logger.error(f"[ChatHistory] Error: {e}\n{traceback.format_exc()}")
        # Return empty history rather than failing — non-critical
        return {"success": True, "history": []}


@router.delete("/history/{document_id}")
async def clear_chat_history(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear chat history for a document."""
    logger.info(f"[ClearHistory] Clearing history for document='{document_id}', user='{current_user.id}'")
    try:
        db.clear_chat_history(document_id, current_user.id)
        return {"success": True, "message": "Chat history cleared"}
    except Exception as e:
        logger.warning(f"[ClearHistory] Failed to clear (non-fatal): {e}")
        return {"success": True, "message": "Chat history cleared"}
