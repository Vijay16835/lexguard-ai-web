"""
Chat Service for LexGuard AI
Provides the business logic layer for RAG-based document Q&A.
Used by the chat API routes.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.chat import ChatHistory
from app.services.groq_service import groq_service


class ChatService:
    """Orchestrates RAG chat: vector search → context building → Groq call → DB save."""

    async def chat_with_document(
        self,
        db: Session,
        document_id: str,
        user_id: int,
        document_text: str,
        query: str
    ) -> Dict[str, Any]:
        """
        RAG Workflow:
        1. Try vector search for relevant chunks.
        2. Fall back to full document text if vector search unavailable.
        3. Build chat history context.
        4. Send to Groq.
        5. Save to DB.
        """
        # 1. Try vector search
        context_chunks = []
        try:
            from app.services.vector_service import vector_service
            context_chunks = await vector_service.search_similar_chunks(
                document_id, query, top_k=4
            )
        except Exception as e:
            print(f"Vector search unavailable: {e}")

        # 2. Build context
        if context_chunks:
            context = "\n\n---\n\n".join(context_chunks)
        else:
            context = document_text[:60000]

        # 3. Get recent history
        recent_chats = db.query(ChatHistory).filter(
            ChatHistory.document_id == document_id,
            ChatHistory.user_id == user_id,
        ).order_by(ChatHistory.created_at.desc()).limit(6).all()

        chat_history = []
        for chat in reversed(recent_chats):
            chat_history.append({"role": "user", "content": chat.query})
            chat_history.append({"role": "assistant", "content": chat.response})

        # 4. Call Groq
        answer = await groq_service.chat_with_document(context, query, chat_history)

        # 5. Save to history
        chat_entry = ChatHistory(
            document_id=document_id,
            user_id=user_id,
            query=query,
            response=answer,
        )
        db.add(chat_entry)
        db.commit()

        return {
            "answer": answer,
            "context_used": context_chunks,
        }


chat_service = ChatService()
