"""Pydantic schemas for services catalog"""
from typing import Optional
from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    category: str
    price: float = 0
    description: Optional[str] = None
    is_active: bool = True


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: str
    clinic_id: str
    name: str
    category: str
    price: float
    description: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


class ServiceListResponse(BaseModel):
    data: list[ServiceResponse]
    total: int
