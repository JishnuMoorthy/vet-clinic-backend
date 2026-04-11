"""Pets routes: list, create, get, update, delete"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.pets import PetCreate, PetListResponse, PetResponse, PetUpdate

router = APIRouter()


def _pet_info_complete(pet: dict) -> bool:
    """A pet record is considered complete if the core identifying
    fields (name, species, breed, gender, date_of_birth) are all filled."""
    return bool(
        pet.get("name")
        and pet.get("species")
        and pet.get("breed")
        and pet.get("gender")
        and pet.get("date_of_birth")
    )


def _build_pet_response(pet: dict, owner_name: str | None = None) -> PetResponse:
    return PetResponse(
        id=str(pet["id"]),
        clinic_id=str(pet["clinic_id"]),
        owner_id=str(pet["owner_id"]),
        name=pet["name"],
        species=pet["species"],
        breed=pet.get("breed"),
        age_years=pet.get("age_years"),
        age_months=pet.get("age_months"),
        weight_kg=pet.get("weight_kg"),
        color=pet.get("color"),
        microchip_id=pet.get("microchip_id"),
        date_of_birth=pet.get("date_of_birth"),
        gender=pet.get("gender"),
        health_status=pet.get("health_status"),
        photo_url=pet.get("photo_url"),
        created_at=str(pet["created_at"]),
        updated_at=str(pet["updated_at"]),
        owner_name=owner_name,
        info_complete=_pet_info_complete(pet),
    )


def _get_owner_name(supabase, owner_id: str) -> str | None:
    result = (
        supabase.table("pet_owners")
        .select("name")
        .eq("id", owner_id)
        .eq("is_deleted", False)
        .execute()
    )
    if result.data:
        return result.data[0]["name"]
    return None


@router.get("", response_model=PetListResponse)
async def list_pets(
    search: str = None,
    owner_id: str = None,
    species: str = None,
    health_status: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    query = (
        supabase.table("pets")
        .select("*", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
    )

    if search:
        query = query.or_(
            f"name.ilike.%{search}%,species.ilike.%{search}%,breed.ilike.%{search}%"
        )
    if owner_id:
        query = query.eq("owner_id", owner_id)
    if species:
        query = query.eq("species", species)
    if health_status:
        query = query.eq("health_status", health_status)

    response = query.range(skip, skip + limit - 1).execute()
    pets = response.data
    total = response.count or 0

    owner_names: dict[str, str] = {}
    if pets:
        unique_owner_ids = list({pet["owner_id"] for pet in pets})
        owners_response = (
            supabase.table("pet_owners")
            .select("id, name")
            .in_("id", unique_owner_ids)
            .eq("is_deleted", False)
            .execute()
        )
        for owner in owners_response.data:
            owner_names[owner["id"]] = owner["name"]

    return PetListResponse(
        data=[_build_pet_response(p, owner_names.get(p["owner_id"])) for p in pets],
        total=total,
    )


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def create_pet(
    pet_in: PetCreate,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    owner_response = (
        supabase.table("pet_owners")
        .select("id, name")
        .eq("id", pet_in.owner_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not owner_response.data:
        raise HTTPException(status_code=404, detail="Owner not found")
    owner_name = owner_response.data[0]["name"]

    new_pet = {"clinic_id": clinic_id, **pet_in.model_dump()}
    response = supabase.table("pets").insert(new_pet).execute()
    return _build_pet_response(response.data[0], owner_name)


@router.get("/{pet_id}", response_model=PetResponse)
async def get_pet(
    pet_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    response = (
        supabase.table("pets")
        .select("*")
        .eq("id", pet_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Pet not found")

    pet = response.data[0]
    return _build_pet_response(pet, _get_owner_name(supabase, pet["owner_id"]))


@router.put("/{pet_id}", response_model=PetResponse)
async def update_pet(
    pet_id: str,
    pet_in: PetUpdate,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("pets")
        .select("*")
        .eq("id", pet_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Pet not found")

    update_data = pet_in.model_dump(exclude_unset=True)

    if "owner_id" in update_data:
        owner_response = (
            supabase.table("pet_owners")
            .select("id")
            .eq("id", update_data["owner_id"])
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .execute()
        )
        if not owner_response.data:
            raise HTTPException(status_code=404, detail="Owner not found")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("pets")
        .update(update_data)
        .eq("id", pet_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )
    pet = response.data[0]
    return _build_pet_response(pet, _get_owner_name(supabase, pet["owner_id"]))


@router.delete("/{pet_id}", response_model=MessageResponse)
async def delete_pet(
    pet_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("pets")
        .select("id")
        .eq("id", pet_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Pet not found")

    supabase.table("pets").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", pet_id).eq("clinic_id", clinic_id).execute()

    return MessageResponse(message="Pet deleted successfully")
