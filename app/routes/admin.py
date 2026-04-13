"""Admin routes: onboard new trial clinics."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, hash_password
from app.database import get_supabase
from app.schemas.onboarding import ClinicOnboardRequest, ClinicOnboardResponse
from app.routes.seed_helpers import seed_services_for_clinic, seed_demo_data_for_clinic

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/onboard-clinic", response_model=ClinicOnboardResponse, status_code=status.HTTP_201_CREATED)
async def onboard_clinic(
    payload: ClinicOnboardRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new trial clinic with an admin user and optional demo data."""

    # Only admins can onboard clinics
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can onboard new clinics.",
        )

    if len(payload.admin_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters.",
        )

    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    # Check email uniqueness
    existing = (
        supabase.table("users")
        .select("id")
        .eq("email", payload.admin_email)
        .execute()
        .data or []
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # Create clinic
    clinic_result = (
        supabase.table("clinics")
        .insert({
            "name": payload.clinic_name,
            "phone": payload.clinic_phone,
            "email": payload.admin_email,
            "created_at": now,
            "updated_at": now,
        })
        .execute()
    )
    if not clinic_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create clinic.",
        )
    clinic = clinic_result.data[0]
    clinic_id = str(clinic["id"])

    # Create admin user
    user_result = (
        supabase.table("users")
        .insert({
            "clinic_id": clinic_id,
            "email": payload.admin_email,
            "name": payload.admin_name,
            "password_hash": hash_password(payload.admin_password),
            "role": "admin",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        })
        .execute()
    )
    if not user_result.data:
        # Rollback clinic creation
        supabase.table("clinics").delete().eq("id", clinic_id).execute()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user.",
        )
    admin_user = user_result.data[0]

    # Always seed services catalog
    svc_count = seed_services_for_clinic(supabase, clinic_id)
    logger.info(f"Seeded {svc_count} services for clinic {clinic_id}")

    # Optionally seed demo data
    demo_summary = {}
    if payload.include_demo_data:
        demo_summary = seed_demo_data_for_clinic(supabase, clinic_id)
        logger.info(f"Seeded demo data for clinic {clinic_id}: {demo_summary}")

    message = f"Clinic '{payload.clinic_name}' created successfully"
    if payload.include_demo_data:
        message += f" with demo data ({demo_summary.get('owners', 0)} owners, {demo_summary.get('pets', 0)} pets, {demo_summary.get('appointments', 0)} appointments, {demo_summary.get('invoices', 0)} invoices)"

    return ClinicOnboardResponse(
        message=message,
        clinic={"id": clinic_id, "name": payload.clinic_name},
        admin={"id": str(admin_user["id"]), "email": payload.admin_email, "name": payload.admin_name},
    )
