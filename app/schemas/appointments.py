"""Pydantic schemas for appointments"""
from typing import Optional
from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    pet_id: str
    owner_id: str
    vet_id: Optional[str] = None
    appointment_date: str
    appointment_time: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "scheduled"


class AppointmentUpdate(BaseModel):
    pet_id: Optional[str] = None
    owner_id: Optional[str] = None
    vet_id: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    clinic_id: str
    pet_id: str
    owner_id: str
    vet_id: Optional[str] = None
    appointment_date: str
    appointment_time: str
    reason: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    pet_name: Optional[str] = None
    owner_name: Optional[str] = None
    vet_name: Optional[str] = None


class AppointmentListResponse(BaseModel):
    data: list[AppointmentResponse]
    total: int
