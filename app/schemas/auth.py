"""Pydantic schemas for authentication"""
from typing import Optional, List
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    clinic_id: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    is_active: bool
    created_at: str
    specialties: List[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    message: str
