from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.api.deps import get_current_user
from app.services.groq_service import groq_service

router = APIRouter()


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
    # 1. Validate document belongs to user and has extracted text
    doc_data = db.get_document(request.document_id)
    if not doc_data or doc_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    extracted_text = doc_data.get("extracted_text")
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Document text not yet extracted. Wait for analysis to complete.")

    try:
        # 2. Try vector search for relevant context
        context_chunks = []
        try:
            from app.services.vector_service import vector_service
            context_chunks = await vector_service.search_similar_chunks(
                request.document_id, request.message, top_k=4
            )
        except Exception as e:
            print(f"Vector search failed, falling back to full text: {e}")

        # 3. Build context — use vector chunks if available, else full text
        if context_chunks:
            context = "\n\n---\n\n".join(context_chunks)
        else:
            # Fallback: use the full extracted text (truncated)
            context = extracted_text[:60000]

        # 4. Get recent chat history for conversational context
        recent_chats = db.get_chat_history(request.document_id, current_user.id)
        # Get only the last 6 entries
        recent_chats = recent_chats[-6:]

        chat_history = []
        for chat in recent_chats:
            chat_history.append({"role": "user", "content": chat["query"]})
            chat_history.append({"role": "assistant", "content": chat["response"]})

        # 5. Call Groq with context + history + query
        answer = await groq_service.chat_with_document(
            context, request.message, chat_history
        )

        # 6. Save to chat history in Firestore
        db.save_chat_entry({
            "document_id": request.document_id,
            "user_id": current_user.id,
            "query": request.message,
            "response": answer,
            "language": "English"
        })

        return {
            "success": True,
            "answer": answer,
            "document_id": request.document_id,
        }
    except Exception as e:
        print(f"Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/history/{document_id}")
async def get_chat_history(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve chat history for a document."""
    chats = db.get_chat_history(document_id, current_user.id)

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


@router.delete("/history/{document_id}")
async def clear_chat_history(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear chat history for a document."""
    db.clear_chat_history(document_id, current_user.id)
    return {"success": True, "message": "Chat history cleared"}
