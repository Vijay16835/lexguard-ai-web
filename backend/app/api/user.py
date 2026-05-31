from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.api import deps
from app.models.user import User
from app.db.session import get_db
from app.core.config import settings
from datetime import datetime
import psycopg2
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

from app.services.document_service import get_user_storage_usage_mb

STORAGE_LIMIT_MB = 10.0

def _get_user_stats_pg(user_id: str) -> dict:
    """Query PostgreSQL for live document count, high-risk count, and AI chat count."""
    stats = {"documents_analyzed": 0, "high_risk_count": 0, "ai_chat_count": 0}
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documents WHERE user_id = %s", (user_id,))
        stats["documents_analyzed"] = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM documents WHERE user_id = %s AND risk_level = 'High'",
            (user_id,)
        )
        stats["high_risk_count"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = %s", (user_id,))
        stats["ai_chat_count"] = cur.fetchone()[0]
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to fetch user stats from PostgreSQL for {user_id}: {e}")
    return stats

@router.get("/me")
async def get_profile(current_user: User = Depends(deps.get_current_user)):
    created_at_val = None
    if current_user.created_at:
        if isinstance(current_user.created_at, datetime):
            created_at_val = current_user.created_at.isoformat()
        else:
            created_at_val = current_user.created_at

    storage_used_mb = get_user_storage_usage_mb(current_user.id)
    stats = _get_user_stats_pg(current_user.id)

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "profile_image": current_user.profile_image,
        "created_at": created_at_val,
        "storage_used_mb": storage_used_mb,
        "storage_limit_mb": STORAGE_LIMIT_MB,
        "documents_analyzed": stats["documents_analyzed"],
        "high_risk_count": stats["high_risk_count"],
        "ai_chat_count": stats["ai_chat_count"],
    }

@router.patch("/settings")
async def update_settings(
    settings_data: dict, 
    current_user: User = Depends(deps.get_current_user),
    db = Depends(get_db)
):
    user_data = db.get_user_by_id(current_user.id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
        
    current_settings = user_data.get("settings", {})
    current_settings.update(settings_data)
    
    db.update_user(current_user.id, {"settings": current_settings})
    return {"message": "Settings updated", "user": current_user.email, "settings": current_settings}

@router.put("/profile")
async def update_profile(
    data: dict,
    current_user: User = Depends(deps.get_current_user),
    db = Depends(get_db)
):
    if "email" in data:
        if data["email"] != current_user.email:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Email cannot be changed after account creation"
                }
            )

    updates = {}
    if "full_name" in data:
        updates["full_name"] = data["full_name"]
    if "profile_image" in data:
        updates["profile_image"] = data["profile_image"]
        
    if updates:
        db.update_user(current_user.id, updates)
        
    # Reload updated user
    updated_user_data = db.get_user_by_id(current_user.id)
    return {"message": "Profile updated", "user": updated_user_data.get("full_name")}
