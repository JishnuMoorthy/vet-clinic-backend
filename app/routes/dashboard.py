"""Dashboard routes: statistics"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.dashboard import DashboardStats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get dashboard statistics for the current user's clinic"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Count pets
    pets_resp = (
        supabase.table("pets")
        .select("id", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    total_pets = pets_resp.count or 0

    # Count owners
    owners_resp = (
        supabase.table("pet_owners")
        .select("id", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    total_owners = owners_resp.count or 0

    # Count appointments
    appts_resp = (
        supabase.table("appointments")
        .select("id", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    total_appointments = appts_resp.count or 0

    # Count upcoming appointments
    upcoming_resp = (
        supabase.table("appointments")
        .select("id", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .eq("status", "scheduled")
        .gte("appointment_date", today)
        .execute()
    )
    upcoming_appointments = upcoming_resp.count or 0

    # Count staff
    staff_resp = (
        supabase.table("users")
        .select("id", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    total_staff = staff_resp.count or 0

    # Count inventory items
    inventory_resp = (
        supabase.table("inventory")
        .select("id", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    total_inventory_items = inventory_resp.count or 0

    # Count low stock items (Python-side comparison)
    all_inventory_resp = (
        supabase.table("inventory")
        .select("id, quantity, low_stock_threshold")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    low_stock_items = sum(
        1
        for item in all_inventory_resp.data
        if item["quantity"] <= (item.get("low_stock_threshold") or 10)
    )

    # Count pending invoices
    pending_resp = (
        supabase.table("invoices")
        .select("id", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .eq("status", "pending")
        .execute()
    )
    pending_invoices = pending_resp.count or 0

    # Sum revenue from paid invoices
    paid_resp = (
        supabase.table("invoices")
        .select("total_amount")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .eq("status", "paid")
        .execute()
    )
    total_revenue = sum(float(inv["total_amount"]) for inv in paid_resp.data) if paid_resp.data else 0.0

    return DashboardStats(
        total_pets=total_pets,
        total_owners=total_owners,
        total_appointments=total_appointments,
        upcoming_appointments=upcoming_appointments,
        total_staff=total_staff,
        total_inventory_items=total_inventory_items,
        low_stock_items=low_stock_items,
        pending_invoices=pending_invoices,
        total_revenue=total_revenue,
    )
