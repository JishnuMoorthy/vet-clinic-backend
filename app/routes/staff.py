"""Staff routes: list, create, get, update, delete"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, hash_password
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.staff import StaffCreate, StaffListResponse, StaffResponse, StaffUpdate

router = APIRouter()


@router.get("", response_model=StaffListResponse)
async def list_staff(
    search: str = None,
    role: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List all staff for the current user's clinic"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    query = (
        supabase.table("users")
        .select("*", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
    )

    if search:
        query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")

    if role:
        query = query.eq("role", role)

    response = query.range(skip, skip + limit - 1).execute()
    staff = response.data
    total = response.count or 0

    staff_responses = []
    for member in staff:
        staff_responses.append(
            StaffResponse(
                id=str(member["id"]),
                clinic_id=str(member["clinic_id"]),
                email=member["email"],
                name=member["name"],
                role=member["role"],
                phone=member.get("phone"),
                is_active=member["is_active"],
                created_at=str(member["created_at"]),
                updated_at=str(member["updated_at"]),
            )
        )

    return StaffListResponse(data=staff_responses, total=total)


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_in: StaffCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new staff member"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage staff",
        )

    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    password_hash = hash_password(staff_in.password)
    new_staff = {
        "clinic_id": clinic_id,
        "email": staff_in.email,
        "name": staff_in.name,
        "password_hash": password_hash,
        "role": staff_in.role,
        "phone": staff_in.phone,
    }
    response = supabase.table("users").insert(new_staff).execute()
    member = response.data[0]

    return StaffResponse(
        id=str(member["id"]),
        clinic_id=str(member["clinic_id"]),
        email=member["email"],
        name=member["name"],
        role=member["role"],
        phone=member.get("phone"),
        is_active=member["is_active"],
        created_at=str(member["created_at"]),
        updated_at=str(member["updated_at"]),
    )


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single staff member by ID"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    response = (
        supabase.table("users")
        .select("*")
        .eq("id", staff_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found",
        )

    member = response.data[0]
    return StaffResponse(
        id=str(member["id"]),
        clinic_id=str(member["clinic_id"]),
        email=member["email"],
        name=member["name"],
        role=member["role"],
        phone=member.get("phone"),
        is_active=member["is_active"],
        created_at=str(member["created_at"]),
        updated_at=str(member["updated_at"]),
    )


@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: str,
    staff_in: StaffUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing staff member"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage staff",
        )

    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("users")
        .select("*")
        .eq("id", staff_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found",
        )

    update_data = staff_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("users")
        .update(update_data)
        .eq("id", staff_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )
    member = response.data[0]

    return StaffResponse(
        id=str(member["id"]),
        clinic_id=str(member["clinic_id"]),
        email=member["email"],
        name=member["name"],
        role=member["role"],
        phone=member.get("phone"),
        is_active=member["is_active"],
        created_at=str(member["created_at"]),
        updated_at=str(member["updated_at"]),
    )


@router.delete("/{staff_id}", response_model=MessageResponse)
async def delete_staff(
    staff_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete a staff member"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage staff",
        )

    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("users")
        .select("id")
        .eq("id", staff_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found",
        )

    supabase.table("users").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", staff_id).eq("clinic_id", clinic_id).execute()

    return MessageResponse(message="Staff member deleted successfully")
