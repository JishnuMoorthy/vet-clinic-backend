"""Pydantic schemas for pet owners"""
from typing import Optional
from pydantic import BaseModel


class OwnerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class OwnerResponse(BaseModel):
    id: str
    clinic_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    created_at: str
    updated_at: str
    pet_count: Optional[int] = 0
    info_complete: bool = True


class OwnerListResponse(BaseModel):
    data: list[OwnerResponse]
    total: int
