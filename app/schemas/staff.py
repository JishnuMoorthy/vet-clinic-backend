"""Pydantic schemas for staff/users"""
from typing import Optional
from pydantic import BaseModel


class StaffCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str
    phone: Optional[str] = None


class StaffUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class StaffResponse(BaseModel):
    id: str
    clinic_id: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


class StaffListResponse(BaseModel):
    data: list[StaffResponse]
    total: int
