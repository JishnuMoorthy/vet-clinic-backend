"""Pydantic schemas for feedback"""
from typing import Optional, Literal
from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    page_path: str
    rating: Optional[Literal["up", "neutral", "down"]] = None
    message: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    clinic_id: str
    user_id: str
    page_path: str
    rating: Optional[str]
    message: Optional[str]
    created_at: str
