"""Inventory routes: list, create, get, update, delete"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.inventory import (
    InventoryCreate,
    InventoryListResponse,
    InventoryResponse,
    InventoryUpdate,
)

router = APIRouter()


def _build_inventory_response(item: dict) -> InventoryResponse:
    """Build an InventoryResponse from a DB row."""
    threshold = item.get("low_stock_threshold") or 10
    is_low_stock = item["quantity"] <= threshold
    return InventoryResponse(
        id=str(item["id"]),
        clinic_id=str(item["clinic_id"]),
        item_name=item["item_name"],
        item_type=item.get("item_type"),
        quantity=item["quantity"],
        unit=item.get("unit"),
        low_stock_threshold=item.get("low_stock_threshold"),
        supplier=item.get("supplier"),
        cost_per_unit=item.get("cost_per_unit"),
        last_restocked_date=str(item["last_restocked_date"]) if item.get("last_restocked_date") else None,
        created_at=str(item["created_at"]),
        updated_at=str(item["updated_at"]),
        is_low_stock=is_low_stock,
    )


@router.get("", response_model=InventoryListResponse)
async def list_inventory(
    search: str = None,
    item_type: str = None,
    low_stock_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List all inventory items for the current user's clinic"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    query = (
        supabase.table("inventory")
        .select("*", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
    )

    if search:
        query = query.ilike("item_name", f"%{search}%")

    if item_type:
        query = query.eq("item_type", item_type)

    if low_stock_only:
        # Fetch all items and filter in Python (column-to-column comparison not supported in Supabase)
        all_resp = query.execute()
        all_items = all_resp.data
        filtered = [_build_inventory_response(item) for item in all_items if _build_inventory_response(item).is_low_stock]
        total = len(filtered)
        return InventoryListResponse(data=filtered[skip: skip + limit], total=total)

    response = query.range(skip, skip + limit - 1).execute()
    items = response.data
    total = response.count or 0

    return InventoryListResponse(data=[_build_inventory_response(item) for item in items], total=total)


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item_in: InventoryCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new inventory item"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    new_item = {"clinic_id": clinic_id, **item_in.model_dump()}
    response = supabase.table("inventory").insert(new_item).execute()
    item = response.data[0]

    return _build_inventory_response(item)


@router.get("/{item_id}", response_model=InventoryResponse)
async def get_inventory_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single inventory item by ID"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    response = (
        supabase.table("inventory")
        .select("*")
        .eq("id", item_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )

    return _build_inventory_response(response.data[0])


@router.put("/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    item_id: str,
    item_in: InventoryUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing inventory item"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("inventory")
        .select("*")
        .eq("id", item_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )

    update_data = item_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("inventory")
        .update(update_data)
        .eq("id", item_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )

    return _build_inventory_response(response.data[0])


@router.delete("/{item_id}", response_model=MessageResponse)
async def delete_inventory_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete an inventory item"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("inventory")
        .select("id")
        .eq("id", item_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )

    supabase.table("inventory").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", item_id).eq("clinic_id", clinic_id).execute()

    return MessageResponse(message="Inventory item deleted successfully")
