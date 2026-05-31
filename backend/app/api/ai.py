from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.api.deps import get_current_user
from app.schemas.ai import QueryRequest
from app.services.groq_service import groq_service
from datetime import datetime, timezone

router = APIRouter()


def _get_user_document(db, document_id: str, user_id: str) -> Document:
    """Helper to fetch a document that belongs to the user."""
    doc_data = db.get_document(document_id)
    if not doc_data or doc_data.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc_data.get("extracted_text"):
        raise HTTPException(status_code=400, detail="Document text not yet extracted. Please wait for analysis to complete.")
    return Document(**doc_data)


@router.post("/analyze/{document_id}")
async def analyze_document(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run full AI analysis on a document (re-analyze)."""
    doc = _get_user_document(db, document_id, current_user.id)
    
    try:
        result = await groq_service.analyze_document(doc.extracted_text)
        
        # Update document in Firestore
        db.update_document(document_id, {
            "risk_score": result.get("risk_score", 0),
            "risk_level": result.get("risk_level", "Medium"),
            "summary": result.get("summary", ""),
            "document_type": result.get("document_type", "Unknown"),
            "status": "completed",
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Update or create analysis in Firestore
        analysis_data = {
            "document_id": document_id,
            "risk_level": result.get("risk_level", "Medium"),
            "risk_score": result.get("risk_score", 0),
            "summary": result.get("summary", ""),
            "ai_confidence": 0.85,
            "parties": result.get("parties", []),
            "important_dates": result.get("important_dates", []),
            "recommendations": result.get("recommendations", []),
            "raw_analysis_data": result,
        }
        db.save_analysis(document_id, analysis_data)
        
        # Update clauses in Firestore
        db.delete_document_clauses(document_id)
        for c_data in result.get("clauses", []):
            db.save_clause({
                "document_id": document_id,
                "title": c_data.get("title", "Untitled"),
                "content": c_data.get("content", ""),
                "summary": c_data.get("explanation", c_data.get("summary", "")),
                "risk_level": c_data.get("risk_level", "Low"),
                "mitigation_advice": c_data.get("mitigation_advice", ""),
            })
        
        return {"success": True, "analysis": result}
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@router.post("/summary/{document_id}")
async def generate_summary(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI summary for a document."""
    doc = _get_user_document(db, document_id, current_user.id)
    
    try:
        result = await groq_service.generate_summary(doc.extracted_text)
        return {"success": True, "summary": result}
    except Exception as e:
        print(f"Summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/risk-analysis/{document_id}")
async def analyze_risk(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dedicated risk analysis for a document."""
    doc = _get_user_document(db, document_id, current_user.id)
    
    try:
        result = await groq_service.analyze_risk(doc.extracted_text)
        return {"success": True, "risk_analysis": result}
    except Exception as e:
        print(f"Risk analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@router.post("/clauses/{document_id}")
async def extract_clauses(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Extract and analyze clauses from a document."""
    doc = _get_user_document(db, document_id, current_user.id)
    
    try:
        clauses = await groq_service.extract_clauses(doc.extracted_text)
        
        # Save to Firestore
        db.delete_document_clauses(document_id)
        for c_data in clauses:
            db.save_clause({
                "document_id": document_id,
                "title": c_data.get("title", "Untitled"),
                "content": c_data.get("content", ""),
                "summary": c_data.get("summary", ""),
                "risk_level": c_data.get("risk_level", "Low"),
                "mitigation_advice": c_data.get("mitigation_advice", ""),
            })
        
        return {"success": True, "clauses": clauses}
    except Exception as e:
        print(f"Clause extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Clause extraction failed: {str(e)}")


@router.post("/chat")
async def chat_with_document(
    request: QueryRequest,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat with a document — ask questions and get AI answers."""
    doc = _get_user_document(db, request.document_id, current_user.id)
    
    try:
        # Get recent chat history for context from Firestore
        recent_chats = db.get_chat_history(request.document_id, current_user.id)
        recent_chats = recent_chats[-6:]
        
        chat_history = []
        for chat in recent_chats:
            chat_history.append({"role": "user", "content": chat["query"]})
            chat_history.append({"role": "assistant", "content": chat["response"]})
        
        # Get AI response
        answer = await groq_service.chat_with_document(
            doc.extracted_text, request.query, chat_history
        )
        
        # Save to chat history in Firestore
        db.save_chat_entry({
            "document_id": request.document_id,
            "user_id": current_user.id,
            "query": request.query,
            "response": answer,
            "language": "English"
        })
        
        return {
            "success": True,
            "answer": answer,
            "document_id": request.document_id,
        }
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/chat-history/{document_id}")
async def get_chat_history(
    document_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chat history for a document."""
    chats = db.get_chat_history(document_id, current_user.id)
    
    return {
        "success": True,
        "history": [
            {
                "id": chat.get("id"),
                "query": chat.get("query"),
                "response": chat.get("response"),
                "created_at": chat.get("created_at"),
            }
            for chat in chats
        ]
    }
