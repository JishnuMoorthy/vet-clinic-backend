"""Reusable seed functions for onboarding new clinics."""
import json
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Services catalog (same as scripts/seed_services.py)
# ---------------------------------------------------------------------------

SERVICES = [
    {"name": "General Consultation",   "category": "consultation", "price": 500,  "description": "Standard 15-minute vet consultation."},
    {"name": "Follow-up Consultation", "category": "consultation", "price": 300,  "description": "Short follow-up visit within 14 days of original consult."},
    {"name": "Emergency Visit",        "category": "consultation", "price": 1500, "description": "After-hours / walk-in emergency consultation."},
    {"name": "Rabies Vaccination",     "category": "vaccination",  "price": 600,  "description": "Single-dose rabies vaccine."},
    {"name": "Core Vaccine (DHPP)",    "category": "vaccination",  "price": 900,  "description": "Distemper, Hepatitis, Parainfluenza, Parvovirus combo."},
    {"name": "Deworming",              "category": "procedure",    "price": 250,  "description": "Broad-spectrum oral dewormer."},
    {"name": "Grooming (Full)",        "category": "grooming",     "price": 1200, "description": "Bath, haircut, nail trim, ear cleaning."},
    {"name": "Dental Cleaning",        "category": "procedure",    "price": 2500, "description": "Scale & polish under light sedation."},
    {"name": "X-Ray (single view)",    "category": "diagnostic",   "price": 1500, "description": "One radiographic view with digital report."},
    {"name": "Complete Blood Test",    "category": "diagnostic",   "price": 1800, "description": "CBC + biochemistry panel."},
    {"name": "Neuter / Spay",          "category": "surgery",      "price": 6000, "description": "Routine neutering or spaying surgery."},
]

# ---------------------------------------------------------------------------
# Demo pet owners
# ---------------------------------------------------------------------------

DEMO_OWNERS = [
    {"name": "Rajesh Kumar",    "email": "rajesh.kumar@example.com",   "phone": "+91-9876543001", "address": "12 MG Road, Bangalore",     "city": "Bangalore", "state": "Karnataka"},
    {"name": "Priya Sharma",    "email": "priya.sharma@example.com",   "phone": "+91-9876543002", "address": "45 Anna Nagar, Chennai",     "city": "Chennai",   "state": "Tamil Nadu"},
    {"name": "Amit Patel",      "email": "amit.patel@example.com",     "phone": "+91-9876543003", "address": "78 Bandra West, Mumbai",     "city": "Mumbai",    "state": "Maharashtra"},
    {"name": "Sneha Reddy",     "email": "sneha.reddy@example.com",    "phone": "+91-9876543004", "address": "23 Jubilee Hills, Hyderabad", "city": "Hyderabad", "state": "Telangana"},
    {"name": "Vikram Singh",    "email": "vikram.singh@example.com",   "phone": "+91-9876543005", "address": "56 Connaught Place, Delhi",   "city": "Delhi",     "state": "Delhi"},
]

# ---------------------------------------------------------------------------
# Demo pets
# ---------------------------------------------------------------------------

DEMO_PETS = [
    {"name": "Bruno",    "species": "dog", "breed": "German Shepherd", "age_years": 3, "weight_kg": 34, "gender": "male",   "health_status": "healthy"},
    {"name": "Whiskers", "species": "cat", "breed": "Persian",        "age_years": 2, "weight_kg": 4,  "gender": "female", "health_status": "healthy"},
    {"name": "Rocky",    "species": "dog", "breed": "Labrador",       "age_years": 5, "weight_kg": 30, "gender": "male",   "health_status": "healthy"},
    {"name": "Luna",     "species": "cat", "breed": "Siamese",        "age_years": 1, "weight_kg": 3,  "gender": "female", "health_status": "healthy"},
    {"name": "Max",      "species": "dog", "breed": "Golden Retriever","age_years": 4, "weight_kg": 32, "gender": "male",  "health_status": "caution"},
    {"name": "Coco",     "species": "dog", "breed": "Pomeranian",     "age_years": 2, "weight_kg": 3,  "gender": "female", "health_status": "healthy"},
    {"name": "Tiger",    "species": "cat", "breed": "Bengal",          "age_years": 3, "weight_kg": 5,  "gender": "male",   "health_status": "healthy"},
    {"name": "Bella",    "species": "dog", "breed": "Beagle",         "age_years": 6, "weight_kg": 12, "gender": "female", "health_status": "caution"},
]

# Pet-to-owner mapping (index into DEMO_OWNERS): owner 0 gets pets 0,1; owner 1 gets pet 2; etc.
PET_OWNER_MAP = [0, 0, 1, 1, 2, 3, 3, 4]


def seed_services_for_clinic(supabase, clinic_id: str) -> int:
    """Seed the services catalog for one clinic. Returns count inserted."""
    existing = (
        supabase.table("services")
        .select("name")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
        .data or []
    )
    existing_names = {row["name"] for row in existing}

    rows = [
        {"clinic_id": clinic_id, **svc, "is_active": True}
        for svc in SERVICES
        if svc["name"] not in existing_names
    ]
    if not rows:
        return 0

    supabase.table("services").insert(rows).execute()
    return len(rows)


def seed_demo_data_for_clinic(supabase, clinic_id: str) -> dict:
    """Seed sample owners, pets, appointments, and invoices for one clinic.
    Returns summary counts."""

    now = datetime.now(timezone.utc)
    counts = {"owners": 0, "pets": 0, "appointments": 0, "invoices": 0}

    # --- Owners ---
    owner_rows = []
    for owner in DEMO_OWNERS:
        owner_rows.append({
            "clinic_id": clinic_id,
            **owner,
        })
    result = supabase.table("pet_owners").insert(owner_rows).execute()
    created_owners = result.data or []
    counts["owners"] = len(created_owners)

    if not created_owners:
        logger.warning("Failed to create demo owners")
        return counts

    # --- Pets ---
    pet_rows = []
    for i, pet in enumerate(DEMO_PETS):
        owner_idx = PET_OWNER_MAP[i]
        pet_rows.append({
            "clinic_id": clinic_id,
            "owner_id": created_owners[owner_idx]["id"],
            **pet,
        })
    result = supabase.table("pets").insert(pet_rows).execute()
    created_pets = result.data or []
    counts["pets"] = len(created_pets)

    if not created_pets:
        logger.warning("Failed to create demo pets")
        return counts

    # --- Appointments ---
    # Fetch the admin user for this clinic to use as vet_id
    admin_user = (
        supabase.table("users")
        .select("id")
        .eq("clinic_id", clinic_id)
        .eq("role", "admin")
        .eq("is_deleted", False)
        .limit(1)
        .execute()
        .data or []
    )
    vet_id = admin_user[0]["id"] if admin_user else None

    appt_statuses = ["completed", "completed", "completed", "completed", "completed",
                     "scheduled", "scheduled", "scheduled", "scheduled", "scheduled",
                     "cancelled", "no_show"]
    appt_reasons = [
        "Annual checkup", "Vaccination", "Skin irritation", "Limping",
        "Routine deworming", "Grooming appointment", "Dental check",
        "Weight concern", "Eye discharge", "Follow-up visit",
        "Ear infection", "Spay consultation",
    ]

    appt_rows = []
    for i in range(12):
        pet = created_pets[i % len(created_pets)]
        days_offset = -20 + (i * 4)  # spread from 20 days ago to ~28 days ahead
        appt_date = (now + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        status = appt_statuses[i % len(appt_statuses)]
        # Past appointments should be completed, future ones scheduled
        if days_offset > 0:
            status = "scheduled"

        appt_rows.append({
            "clinic_id": clinic_id,
            "pet_id": pet["id"],
            "owner_id": pet["owner_id"],
            "vet_id": vet_id,
            "appointment_date": appt_date,
            "appointment_time": f"{9 + (i % 8)}:{'00' if i % 2 == 0 else '30'}",
            "reason": appt_reasons[i % len(appt_reasons)],
            "status": status,
            "notes": f"Demo appointment for {pet['name']}",
        })

    result = supabase.table("appointments").insert(appt_rows).execute()
    counts["appointments"] = len(result.data or [])

    # --- Invoices ---
    services = (
        supabase.table("services")
        .select("id, name, price, category")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .eq("is_active", True)
        .execute()
        .data or []
    )
    svc_lookup = {s["name"]: s for s in services}

    scenarios = [
        (["General Consultation", "Rabies Vaccination"], "paid", 40, "Annual checkup and rabies shot"),
        (["General Consultation", "Core Vaccine (DHPP)"], "paid", 35, "Puppy vaccination visit"),
        (["Emergency Visit", "X-Ray (single view)", "Complete Blood Test"], "paid", 30, "Emergency after vomiting"),
        (["General Consultation", "Deworming"], "paid", 25, "Routine deworming"),
        (["Grooming (Full)"], "paid", 20, "Full grooming session"),
        (["Dental Cleaning", "General Consultation"], "pending", 12, "Dental cleaning under sedation"),
        (["General Consultation", "Complete Blood Test"], "pending", 8, "Senior pet wellness check"),
        (["Follow-up Consultation", "Deworming"], "pending", 5, "Follow-up after treatment"),
        (["Emergency Visit", "X-Ray (single view)"], "overdue", 18, "Limping — suspected fracture"),
        (["Neuter / Spay", "General Consultation"], "pending", 3, "Spay surgery pre-op"),
    ]

    # Generate unique invoice numbers using clinic_id prefix
    clinic_prefix = clinic_id[:4].upper()
    invoices_created = 0

    for i, (svc_names, status, days_ago, notes) in enumerate(scenarios):
        pet = created_pets[i % len(created_pets)]
        issue_date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        due_date = (now - timedelta(days=days_ago - 14)).strftime("%Y-%m-%d")

        line_items = []
        subtotal = 0
        for svc_name in svc_names:
            svc = svc_lookup.get(svc_name)
            if not svc:
                continue
            item = {
                "description": svc["name"],
                "quantity": 1,
                "unit_price": svc["price"],
                "total": svc["price"],
            }
            line_items.append(item)
            subtotal += item["total"]

        if not line_items:
            continue

        discount = round(subtotal * 0.1) if i in (0, 2, 9) else 0
        total = subtotal - discount
        invoice_number = f"INV-{clinic_prefix}-{str(i + 1).zfill(3)}"

        row = {
            "clinic_id": clinic_id,
            "owner_id": pet["owner_id"],
            "pet_id": pet["id"],
            "invoice_number": invoice_number,
            "amount": subtotal,
            "tax_amount": 0,
            "total_amount": total,
            "discount": discount,
            "line_items": json.dumps(line_items),
            "status": status,
            "due_date": due_date,
            "issue_date": issue_date,
            "notes": notes,
            "is_deleted": False,
        }

        supabase.table("invoices").insert(row).execute()
        invoices_created += 1

    counts["invoices"] = invoices_created
    return counts
