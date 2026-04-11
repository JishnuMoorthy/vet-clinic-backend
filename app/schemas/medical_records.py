"""Pydantic schemas for medical records"""
from typing import Optional
from pydantic import BaseModel


class MedicalRecordCreate(BaseModel):
    pet_id: str
    vet_id: str
    appointment_id: Optional[str] = None
    record_date: str
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None


class MedicalRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None
    record_date: Optional[str] = None


class MedicalRecordResponse(BaseModel):
    id: str
    clinic_id: str
    pet_id: str
    vet_id: str
    appointment_id: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None
    record_date: str
    created_at: str
    updated_at: str


class MedicalRecordListResponse(BaseModel):
    data: list[MedicalRecordResponse]
    total: int
