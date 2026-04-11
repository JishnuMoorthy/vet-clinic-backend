"""Appointments routes: list, create, get, update, delete"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.appointments import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentUpdate,
)

router = APIRouter()


def _build_appointment_response(appt: dict, pet_info: dict, owner_info: dict, vet_names: dict) -> AppointmentResponse:
    """Build an AppointmentResponse from a DB row and lookup dicts."""
    pid = str(appt["pet_id"])
    oid = str(appt["owner_id"])
    pet = pet_info.get(pid, {})
    owner = owner_info.get(oid, {})
    return AppointmentResponse(
        id=str(appt["id"]),
        clinic_id=str(appt["clinic_id"]),
        pet_id=pid,
        owner_id=oid,
        vet_id=str(appt["vet_id"]) if appt.get("vet_id") else None,
        appointment_date=str(appt["appointment_date"]),
        appointment_time=str(appt["appointment_time"]),
        reason=appt.get("reason"),
        status=appt.get("status"),
        notes=appt.get("notes"),
        created_at=str(appt["created_at"]),
        updated_at=str(appt["updated_at"]),
        pet_name=pet.get("name"),
        pet_species=pet.get("species"),
        pet_breed=pet.get("breed"),
        pet_photo_url=pet.get("photo_url"),
        owner_name=owner.get("name"),
        owner_phone=owner.get("phone"),
        vet_name=vet_names.get(str(appt["vet_id"])) if appt.get("vet_id") else None,
    )


def _fetch_names(supabase, appointments: list) -> tuple[dict, dict, dict]:
    """Batch-fetch pet info, owner info, and vet names for a list of appointment rows."""
    pet_ids = list({str(a["pet_id"]) for a in appointments if a.get("pet_id")})
    owner_ids = list({str(a["owner_id"]) for a in appointments if a.get("owner_id")})
    vet_ids = list({str(a["vet_id"]) for a in appointments if a.get("vet_id")})

    pet_info: dict = {}
    if pet_ids:
        pets = (
            supabase.table("pets")
            .select("id, name, species, breed, photo_url")
            .in_("id", pet_ids)
            .execute()
        )
        pet_info = {str(p["id"]): p for p in pets.data}

    owner_info: dict = {}
    if owner_ids:
        owners = (
            supabase.table("pet_owners")
            .select("id, name, phone")
            .in_("id", owner_ids)
            .execute()
        )
        owner_info = {str(o["id"]): o for o in owners.data}

    vet_names: dict = {}
    if vet_ids:
        vets = supabase.table("users").select("id, name").in_("id", vet_ids).execute()
        vet_names = {str(v["id"]): v["name"] for v in vets.data}

    return pet_info, owner_info, vet_names


@router.get("", response_model=AppointmentListResponse)
async def list_appointments(
    status: str = None,
    pet_id: str = None,
    owner_id: str = None,
    vet_id: str = None,
    date_from: str = None,
    date_to: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List all appointments for the current user's clinic"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    query = (
        supabase.table("appointments")
        .select("*", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
    )

    if status:
        query = query.eq("status", status)
    if pet_id:
        query = query.eq("pet_id", pet_id)
    if owner_id:
        query = query.eq("owner_id", owner_id)
    if vet_id:
        query = query.eq("vet_id", vet_id)
    if date_from:
        query = query.gte("appointment_date", date_from)
    if date_to:
        query = query.lte("appointment_date", date_to)

    response = query.range(skip, skip + limit - 1).execute()
    appointments = response.data
    total = response.count or 0

    pet_names, owner_names, vet_names = _fetch_names(supabase, appointments)

    return AppointmentListResponse(
        data=[_build_appointment_response(a, pet_names, owner_names, vet_names) for a in appointments],
        total=total,
    )


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appt_in: AppointmentCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new appointment"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    # Validate pet
    pet_resp = (
        supabase.table("pets")
        .select("id, name")
        .eq("id", appt_in.pet_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not pet_resp.data:
        raise HTTPException(status_code=404, detail="Pet not found")

    # Validate owner
    owner_resp = (
        supabase.table("pet_owners")
        .select("id, name")
        .eq("id", appt_in.owner_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not owner_resp.data:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Validate vet if provided
    if appt_in.vet_id:
        vet_resp = (
            supabase.table("users")
            .select("id, name")
            .eq("id", appt_in.vet_id)
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .execute()
        )
        if not vet_resp.data:
            raise HTTPException(status_code=404, detail="Vet not found")

    new_appt = {"clinic_id": clinic_id, **appt_in.model_dump()}
    response = supabase.table("appointments").insert(new_appt).execute()
    appt = response.data[0]

    pet_names, owner_names, vet_names = _fetch_names(supabase, [appt])
    return _build_appointment_response(appt, pet_names, owner_names, vet_names)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single appointment by ID"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    response = (
        supabase.table("appointments")
        .select("*")
        .eq("id", appointment_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt = response.data[0]
    pet_names, owner_names, vet_names = _fetch_names(supabase, [appt])
    return _build_appointment_response(appt, pet_names, owner_names, vet_names)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    appt_in: AppointmentUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing appointment"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("appointments")
        .select("*")
        .eq("id", appointment_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_data = appt_in.model_dump(exclude_unset=True)

    # Validate foreign keys if being changed
    if "pet_id" in update_data:
        pet_resp = (
            supabase.table("pets")
            .select("id")
            .eq("id", update_data["pet_id"])
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .execute()
        )
        if not pet_resp.data:
            raise HTTPException(status_code=404, detail="Pet not found")

    if "owner_id" in update_data:
        owner_resp = (
            supabase.table("pet_owners")
            .select("id")
            .eq("id", update_data["owner_id"])
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .execute()
        )
        if not owner_resp.data:
            raise HTTPException(status_code=404, detail="Owner not found")

    if "vet_id" in update_data and update_data["vet_id"]:
        vet_resp = (
            supabase.table("users")
            .select("id")
            .eq("id", update_data["vet_id"])
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .execute()
        )
        if not vet_resp.data:
            raise HTTPException(status_code=404, detail="Vet not found")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("appointments")
        .update(update_data)
        .eq("id", appointment_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )
    appt = response.data[0]

    pet_names, owner_names, vet_names = _fetch_names(supabase, [appt])
    return _build_appointment_response(appt, pet_names, owner_names, vet_names)


@router.delete("/{appointment_id}", response_model=MessageResponse)
async def delete_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete an appointment"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("appointments")
        .select("id")
        .eq("id", appointment_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    supabase.table("appointments").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", appointment_id).eq("clinic_id", clinic_id).execute()

    return MessageResponse(message="Appointment deleted successfully")
