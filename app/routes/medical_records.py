"""Medical records routes: list, create, get, update, delete"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.medical_records import (
    MedicalRecordCreate,
    MedicalRecordListResponse,
    MedicalRecordResponse,
    MedicalRecordUpdate,
)

router = APIRouter()


def _build(r: dict) -> MedicalRecordResponse:
    return MedicalRecordResponse(
        id=str(r["id"]),
        clinic_id=str(r["clinic_id"]),
        pet_id=str(r["pet_id"]),
        vet_id=str(r["vet_id"]),
        appointment_id=str(r["appointment_id"]) if r.get("appointment_id") else None,
        diagnosis=r.get("diagnosis"),
        treatment=r.get("treatment"),
        notes=r.get("notes"),
        record_date=str(r["record_date"]),
        created_at=str(r["created_at"]),
        updated_at=str(r["updated_at"]),
    )


@router.get("", response_model=MedicalRecordListResponse)
async def list_medical_records(
    pet_id: str = None,
    date_from: str = None,
    date_to: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]
    query = (
        supabase.table("medical_records")
        .select("*", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
    )
    if pet_id:
        query = query.eq("pet_id", pet_id)
    if date_from:
        query = query.gte("record_date", date_from)
    if date_to:
        query = query.lte("record_date", date_to)
    resp = query.order("record_date", desc=True).range(skip, skip + limit - 1).execute()
    return MedicalRecordListResponse(
        data=[_build(r) for r in (resp.data or [])],
        total=resp.count or 0,
    )


@router.post("", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    rec_in: MedicalRecordCreate,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]
    new_rec = {"clinic_id": clinic_id, **rec_in.model_dump(exclude_none=True)}
    resp = supabase.table("medical_records").insert(new_rec).execute()
    return _build(resp.data[0])


@router.get("/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record(
    record_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]
    resp = (
        supabase.table("medical_records")
        .select("*")
        .eq("id", record_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return _build(resp.data[0])


@router.put("/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    record_id: str,
    rec_in: MedicalRecordUpdate,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]
    existing = (
        supabase.table("medical_records")
        .select("id")
        .eq("id", record_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Medical record not found")
    update_data = rec_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    resp = (
        supabase.table("medical_records")
        .update(update_data)
        .eq("id", record_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )
    return _build(resp.data[0])


@router.delete("/{record_id}", response_model=MessageResponse)
async def delete_medical_record(
    record_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]
    existing = (
        supabase.table("medical_records")
        .select("id")
        .eq("id", record_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Medical record not found")
    supabase.table("medical_records").update(
        {"is_deleted": True, "deleted_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", record_id).eq("clinic_id", clinic_id).execute()
    return MessageResponse(message="Medical record deleted successfully")
