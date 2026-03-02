"""Pet Owners routes: list, create, get, update, delete"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.owners import OwnerCreate, OwnerListResponse, OwnerResponse, OwnerUpdate

router = APIRouter()


def _get_pet_count(supabase, owner_id: str) -> int:
    """Return the number of non-deleted pets for a given owner."""
    result = (
        supabase.table("pets")
        .select("id", count="exact")
        .eq("owner_id", owner_id)
        .eq("is_deleted", False)
        .execute()
    )
    return result.count or 0


@router.get("", response_model=OwnerListResponse)
async def list_owners(
    search: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List all owners for the current user's clinic"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    query = (
        supabase.table("pet_owners")
        .select("*", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
    )

    if search:
        query = query.or_(
            f"name.ilike.%{search}%,email.ilike.%{search}%,phone.ilike.%{search}%"
        )

    response = query.range(skip, skip + limit - 1).execute()
    owners = response.data
    total = response.count or 0

    # Fetch pet counts for all owners in one query to avoid N+1
    pet_counts: dict[str, int] = {}
    if owners:
        owner_ids = [owner["id"] for owner in owners]
        pets_response = (
            supabase.table("pets")
            .select("owner_id", count="exact")
            .in_("owner_id", owner_ids)
            .eq("is_deleted", False)
            .execute()
        )
        for pet in pets_response.data:
            oid = pet["owner_id"]
            pet_counts[oid] = pet_counts.get(oid, 0) + 1

    owner_responses = []
    for owner in owners:
        owner_responses.append(
            OwnerResponse(
                id=str(owner["id"]),
                clinic_id=str(owner["clinic_id"]),
                name=owner["name"],
                email=owner.get("email"),
                phone=owner.get("phone"),
                address=owner.get("address"),
                city=owner.get("city"),
                state=owner.get("state"),
                zip_code=owner.get("zip_code"),
                created_at=str(owner["created_at"]),
                updated_at=str(owner["updated_at"]),
                pet_count=pet_counts.get(owner["id"], 0),
            )
        )

    return OwnerListResponse(data=owner_responses, total=total)


@router.post("", response_model=OwnerResponse, status_code=status.HTTP_201_CREATED)
async def create_owner(
    owner_in: OwnerCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new pet owner"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    new_owner = {"clinic_id": clinic_id, **owner_in.model_dump()}
    response = supabase.table("pet_owners").insert(new_owner).execute()
    owner = response.data[0]

    return OwnerResponse(
        id=str(owner["id"]),
        clinic_id=str(owner["clinic_id"]),
        name=owner["name"],
        email=owner.get("email"),
        phone=owner.get("phone"),
        address=owner.get("address"),
        city=owner.get("city"),
        state=owner.get("state"),
        zip_code=owner.get("zip_code"),
        created_at=str(owner["created_at"]),
        updated_at=str(owner["updated_at"]),
        pet_count=0,
    )


@router.get("/{owner_id}", response_model=OwnerResponse)
async def get_owner(
    owner_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single pet owner by ID"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    response = (
        supabase.table("pet_owners")
        .select("*")
        .eq("id", owner_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    owners = response.data
    if not owners:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found",
        )

    owner = owners[0]
    pet_count = _get_pet_count(supabase, owner["id"])
    return OwnerResponse(
        id=str(owner["id"]),
        clinic_id=str(owner["clinic_id"]),
        name=owner["name"],
        email=owner.get("email"),
        phone=owner.get("phone"),
        address=owner.get("address"),
        city=owner.get("city"),
        state=owner.get("state"),
        zip_code=owner.get("zip_code"),
        created_at=str(owner["created_at"]),
        updated_at=str(owner["updated_at"]),
        pet_count=pet_count,
    )


@router.put("/{owner_id}", response_model=OwnerResponse)
async def update_owner(
    owner_id: str,
    owner_in: OwnerUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing pet owner"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("pet_owners")
        .select("*")
        .eq("id", owner_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found",
        )

    update_data = owner_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("pet_owners")
        .update(update_data)
        .eq("id", owner_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )
    owner = response.data[0]

    pet_count = _get_pet_count(supabase, owner["id"])
    return OwnerResponse(
        id=str(owner["id"]),
        clinic_id=str(owner["clinic_id"]),
        name=owner["name"],
        email=owner.get("email"),
        phone=owner.get("phone"),
        address=owner.get("address"),
        city=owner.get("city"),
        state=owner.get("state"),
        zip_code=owner.get("zip_code"),
        created_at=str(owner["created_at"]),
        updated_at=str(owner["updated_at"]),
        pet_count=pet_count,
    )


@router.delete("/{owner_id}", response_model=MessageResponse)
async def delete_owner(
    owner_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete a pet owner"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("pet_owners")
        .select("id")
        .eq("id", owner_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found",
        )

    supabase.table("pet_owners").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", owner_id).eq("clinic_id", clinic_id).execute()

    return MessageResponse(message="Owner deleted successfully")
