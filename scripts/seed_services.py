"""Seed the services table with realistic vet clinic services.

Run once the 003_create_services.sql migration has been applied:
    python -m scripts.seed_services

Inserts the same catalog for every clinic. Skips rows that already
exist (matched by clinic_id + name) so it is idempotent.
"""
from app.database import get_supabase


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


def main() -> None:
    supabase = get_supabase()

    clinics = supabase.table("clinics").select("id, name").execute().data or []
    if not clinics:
        print("No clinics found — seed aborted.")
        return

    total_inserted = 0
    for clinic in clinics:
        clinic_id = clinic["id"]
        existing = (
            supabase.table("services")
            .select("name")
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .execute()
            .data
            or []
        )
        existing_names = {row["name"] for row in existing}

        rows = [
            {"clinic_id": clinic_id, **svc, "is_active": True}
            for svc in SERVICES
            if svc["name"] not in existing_names
        ]
        if not rows:
            print(f"• {clinic['name']}: already seeded, skipping.")
            continue

        supabase.table("services").insert(rows).execute()
        total_inserted += len(rows)
        print(f"• {clinic['name']}: inserted {len(rows)} services.")

    print(f"\nDone. {total_inserted} rows inserted across {len(clinics)} clinic(s).")


if __name__ == "__main__":
    main()
