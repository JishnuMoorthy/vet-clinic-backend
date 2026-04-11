"""Services catalog routes: list, create, get, update, delete"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.services import (
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
    ServiceUpdate,
)

router = APIRouter()


def _build_service_response(svc: dict) -> ServiceResponse:
    return ServiceResponse(
        id=str(svc["id"]),
        clinic_id=str(svc["clinic_id"]),
        name=svc["name"],
        category=svc["category"],
        price=float(svc.get("price") or 0),
        description=svc.get("description"),
        is_active=bool(svc.get("is_active", True)),
        created_at=str(svc["created_at"]),
        updated_at=str(svc["updated_at"]),
    )


@router.get("", response_model=ServiceListResponse)
async def list_services(
    search: str = None,
    category: str = None,
    is_active: bool = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    query = (
        supabase.table("services")
        .select("*", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
    )

    if search:
        query = query.or_(
            f"name.ilike.%{search}%,description.ilike.%{search}%,category.ilike.%{search}%"
        )
    if category:
        query = query.eq("category", category)
    if is_active is not None:
        query = query.eq("is_active", is_active)

    response = query.order("name").range(skip, skip + limit - 1).execute()
    return ServiceListResponse(
        data=[_build_service_response(s) for s in response.data],
        total=response.count or 0,
    )


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    svc_in: ServiceCreate,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    new_svc = {"clinic_id": clinic_id, **svc_in.model_dump()}
    response = supabase.table("services").insert(new_svc).execute()
    return _build_service_response(response.data[0])


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    response = (
        supabase.table("services")
        .select("*")
        .eq("id", service_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Service not found")
    return _build_service_response(response.data[0])


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    svc_in: ServiceUpdate,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("services")
        .select("id")
        .eq("id", service_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Service not found")

    update_data = svc_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("services")
        .update(update_data)
        .eq("id", service_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )
    return _build_service_response(response.data[0])


@router.delete("/{service_id}", response_model=MessageResponse)
async def delete_service(
    service_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("services")
        .select("id")
        .eq("id", service_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Service not found")

    supabase.table("services").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", service_id).eq("clinic_id", clinic_id).execute()

    return MessageResponse(message="Service deleted successfully")
