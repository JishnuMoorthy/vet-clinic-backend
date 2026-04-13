"""Seed realistic invoices with line items from the services catalog.

Run after services are seeded:
    python -m scripts.seed_invoices

Deletes all existing invoices (soft-deleted or not) for every clinic,
then creates 10 fresh invoices with proper line items derived from the
services table, assigned to real pets and owners.
"""
import json
import random
from datetime import datetime, timedelta, timezone

from app.database import get_supabase


def main() -> None:
    supabase = get_supabase()

    clinics = supabase.table("clinics").select("id, name").execute().data or []
    if not clinics:
        print("No clinics found — seed aborted.")
        return

    for clinic in clinics:
        clinic_id = clinic["id"]
        print(f"\n--- {clinic['name']} (clinic_id={clinic_id}) ---")

        # Fetch services for this clinic
        services = (
            supabase.table("services")
            .select("id, name, price, category")
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .eq("is_active", True)
            .execute()
            .data or []
        )
        if not services:
            print("  No services found — skipping. Run seed_services first.")
            continue

        # Fetch pets with their owners
        pets = (
            supabase.table("pets")
            .select("id, name, owner_id")
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .limit(20)
            .execute()
            .data or []
        )
        if not pets:
            print("  No pets found — skipping.")
            continue

        # Fetch owners to validate
        owner_ids = list({p["owner_id"] for p in pets if p.get("owner_id")})
        owners = (
            supabase.table("pet_owners")
            .select("id, name")
            .in_("id", owner_ids)
            .execute()
            .data or []
        )
        owner_map = {o["id"]: o["name"] for o in owners}

        # Filter pets to those with valid owners
        valid_pets = [p for p in pets if p.get("owner_id") in owner_map]
        if not valid_pets:
            print("  No pets with valid owners — skipping.")
            continue

        # Delete existing invoices for this clinic
        existing = (
            supabase.table("invoices")
            .select("id")
            .eq("clinic_id", clinic_id)
            .execute()
            .data or []
        )
        if existing:
            ids = [e["id"] for e in existing]
            for inv_id in ids:
                supabase.table("invoices").delete().eq("id", inv_id).execute()
            print(f"  Deleted {len(ids)} old invoices.")

        # Build service lookup by category for realistic combos
        svc_by_cat = {}
        for s in services:
            svc_by_cat.setdefault(s["category"], []).append(s)

        # Define 10 invoice scenarios (realistic vet visit combos)
        scenarios = [
            # (services to pick, status, days_ago for issue, notes)
            (["General Consultation", "Rabies Vaccination"], "paid", 40, "Annual checkup and rabies shot"),
            (["General Consultation", "Core Vaccine (DHPP)"], "paid", 35, "Puppy vaccination visit"),
            (["Emergency Visit", "X-Ray (single view)", "Complete Blood Test"], "paid", 30, "Emergency after vomiting episode"),
            (["General Consultation", "Deworming"], "paid", 25, "Routine deworming"),
            (["Grooming (Full)"], "paid", 20, "Full grooming session"),
            (["Dental Cleaning", "General Consultation"], "pending", 12, "Dental cleaning under sedation"),
            (["General Consultation", "Complete Blood Test"], "pending", 8, "Senior pet wellness check"),
            (["Follow-up Consultation", "Deworming"], "pending", 5, "Follow-up after treatment"),
            (["Emergency Visit", "X-Ray (single view)"], "overdue", 18, "Limping — suspected fracture"),
            (["Neuter / Spay", "General Consultation"], "pending", 3, "Spay surgery pre-op and procedure"),
        ]

        svc_lookup = {s["name"]: s for s in services}
        now = datetime.now(timezone.utc)
        invoices_created = 0

        for i, (svc_names, status, days_ago, notes) in enumerate(scenarios):
            pet = valid_pets[i % len(valid_pets)]
            issue_date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            due_date = (now - timedelta(days=days_ago - 14)).strftime("%Y-%m-%d")

            line_items = []
            subtotal = 0
            for svc_name in svc_names:
                svc = svc_lookup.get(svc_name)
                if not svc:
                    continue
                qty = 1
                item = {
                    "description": svc["name"],
                    "quantity": qty,
                    "unit_price": svc["price"],
                    "total": svc["price"] * qty,
                }
                line_items.append(item)
                subtotal += item["total"]

            if not line_items:
                continue

            # Apply small discount on some invoices
            discount = 0
            if i in (0, 2, 9):
                discount = round(subtotal * 0.1)  # 10% discount

            total = subtotal - discount
            invoice_number = f"INV-2026-{str(i + 1).zfill(3)}"

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
            pet_name = pet["name"]
            owner_name = owner_map.get(pet["owner_id"], "?")
            print(f"  {invoice_number}: {pet_name} ({owner_name}) — {', '.join(svc_names)} — ₹{total} [{status}]")

        print(f"  Created {invoices_created} invoices.")

    print("\nDone.")


if __name__ == "__main__":
    main()
