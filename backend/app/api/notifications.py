from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_notifications():
    return [{"id": 1, "title": "Analysis Complete", "message": "Document NDA.pdf is ready."}]
