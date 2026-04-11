"""Feedback routes: submit trial user feedback"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: dict = Depends(get_current_user),
):
    """Record feedback submitted by a trial user."""
    if not payload.rating and not (payload.message and payload.message.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least a rating or a message.",
        )

    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    row = {
        "clinic_id": current_user["clinic_id"],
        "user_id": current_user["id"],
        "page_path": payload.page_path,
        "rating": payload.rating,
        "message": payload.message,
        "created_at": now,
    }

    result = supabase.table("feedback").insert(row).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save feedback.",
        )

    saved = result.data[0]
    return FeedbackResponse(
        id=str(saved["id"]),
        clinic_id=str(saved["clinic_id"]),
        user_id=str(saved["user_id"]),
        page_path=saved["page_path"],
        rating=saved.get("rating"),
        message=saved.get("message"),
        created_at=str(saved["created_at"]),
    )
