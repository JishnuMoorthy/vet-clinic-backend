"""Pets routes: list, create, get, update, delete"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.pets import PetCreate, PetListResponse, PetResponse, PetUpdate

router = APIRouter()


def _get_owner_name(supabase, owner_id: str) -> str | None:
    """Return the name of the owner for a given owner_id."""
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
    """List all pets for the current user's clinic"""
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

    # Batch-fetch owner names to avoid N+1 queries
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

    pet_responses = []
    for pet in pets:
        pet_responses.append(
            PetResponse(
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
                created_at=str(pet["created_at"]),
                updated_at=str(pet["updated_at"]),
                owner_name=owner_names.get(pet["owner_id"]),
            )
        )

    return PetListResponse(data=pet_responses, total=total)


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def create_pet(
    pet_in: PetCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new pet"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    # Validate owner exists in the same clinic
    owner_response = (
        supabase.table("pet_owners")
        .select("id, name")
        .eq("id", pet_in.owner_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not owner_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found",
        )
    owner_name = owner_response.data[0]["name"]

    new_pet = {"clinic_id": clinic_id, **pet_in.model_dump()}
    response = supabase.table("pets").insert(new_pet).execute()
    pet = response.data[0]

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
        created_at=str(pet["created_at"]),
        updated_at=str(pet["updated_at"]),
        owner_name=owner_name,
    )


@router.get("/{pet_id}", response_model=PetResponse)
async def get_pet(
    pet_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single pet by ID"""
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
    pets = response.data
    if not pets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found",
        )

    pet = pets[0]
    owner_name = _get_owner_name(supabase, pet["owner_id"])
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
        created_at=str(pet["created_at"]),
        updated_at=str(pet["updated_at"]),
        owner_name=owner_name,
    )


@router.put("/{pet_id}", response_model=PetResponse)
async def update_pet(
    pet_id: str,
    pet_in: PetUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing pet"""
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found",
        )

    update_data = pet_in.model_dump(exclude_unset=True)

    # If owner_id is being updated, validate the new owner exists
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Owner not found",
            )

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("pets")
        .update(update_data)
        .eq("id", pet_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )
    pet = response.data[0]

    owner_name = _get_owner_name(supabase, pet["owner_id"])
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
        created_at=str(pet["created_at"]),
        updated_at=str(pet["updated_at"]),
        owner_name=owner_name,
    )


@router.delete("/{pet_id}", response_model=MessageResponse)
async def delete_pet(
    pet_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete a pet"""
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found",
        )

    supabase.table("pets").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", pet_id).eq("clinic_id", clinic_id).execute()

    return MessageResponse(message="Pet deleted successfully")
