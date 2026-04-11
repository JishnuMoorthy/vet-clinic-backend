"""Pydantic schemas for pets"""
from typing import Optional
from pydantic import BaseModel


class PetCreate(BaseModel):
    owner_id: str
    name: str
    species: str
    breed: Optional[str] = None
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    weight_kg: Optional[float] = None
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    health_status: Optional[str] = "healthy"
    photo_url: Optional[str] = None


class PetUpdate(BaseModel):
    owner_id: Optional[str] = None
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    weight_kg: Optional[float] = None
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    health_status: Optional[str] = None
    photo_url: Optional[str] = None


class PetResponse(BaseModel):
    id: str
    clinic_id: str
    owner_id: str
    name: str
    species: str
    breed: Optional[str] = None
    age_years: Optional[int] = None
    age_months: Optional[int] = None
    weight_kg: Optional[float] = None
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    health_status: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: str
    updated_at: str
    owner_name: Optional[str] = None
    info_complete: bool = True


class PetListResponse(BaseModel):
    data: list[PetResponse]
    total: int
