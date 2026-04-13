"""Invoices & Billing routes: list, create, get, update, delete, payments"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.database import get_supabase
from app.schemas.auth import MessageResponse
from app.schemas.invoices import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
    PaymentCreate,
    PaymentListResponse,
    PaymentResponse,
)

router = APIRouter()


def _build_invoice_response(invoice: dict, owner_names: dict, pet_names: dict) -> InvoiceResponse:
    """Build an InvoiceResponse from a DB row and name lookup dicts."""
    return InvoiceResponse(
        id=str(invoice["id"]),
        clinic_id=str(invoice["clinic_id"]),
        owner_id=str(invoice["owner_id"]),
        pet_id=str(invoice["pet_id"]),
        appointment_id=str(invoice["appointment_id"]) if invoice.get("appointment_id") else None,
        invoice_number=invoice["invoice_number"],
        amount=float(invoice["amount"]),
        tax_amount=float(invoice["tax_amount"]) if invoice.get("tax_amount") is not None else None,
        total_amount=float(invoice["total_amount"]),
        status=invoice.get("status"),
        due_date=str(invoice["due_date"]) if invoice.get("due_date") else None,
        issue_date=str(invoice["issue_date"]),
        notes=invoice.get("notes"),
        created_at=str(invoice["created_at"]),
        updated_at=str(invoice["updated_at"]),
        line_items=json.loads(invoice["line_items"]) if isinstance(invoice.get("line_items"), str) else (invoice.get("line_items") or []),
        discount=float(invoice.get("discount") or 0),
        owner_name=owner_names.get(str(invoice["owner_id"])),
        pet_name=pet_names.get(str(invoice["pet_id"])),
    )


def _fetch_invoice_names(supabase, invoices: list) -> tuple[dict, dict]:
    """Batch-fetch owner and pet names for a list of invoice rows."""
    owner_ids = list({str(inv["owner_id"]) for inv in invoices if inv.get("owner_id")})
    pet_ids = list({str(inv["pet_id"]) for inv in invoices if inv.get("pet_id")})

    owner_names: dict = {}
    if owner_ids:
        owners = supabase.table("pet_owners").select("id, name").in_("id", owner_ids).execute()
        owner_names = {str(o["id"]): o["name"] for o in owners.data}

    pet_names: dict = {}
    if pet_ids:
        pets = supabase.table("pets").select("id, name").in_("id", pet_ids).execute()
        pet_names = {str(p["id"]): p["name"] for p in pets.data}

    return owner_names, pet_names


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    status: str = None,
    owner_id: str = None,
    pet_id: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List all invoices for the current user's clinic"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    query = (
        supabase.table("invoices")
        .select("*", count="exact")
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
    )

    if status:
        query = query.eq("status", status)
    if owner_id:
        query = query.eq("owner_id", owner_id)
    if pet_id:
        query = query.eq("pet_id", pet_id)

    response = query.range(skip, skip + limit - 1).execute()
    invoices = response.data
    total = response.count or 0

    owner_names, pet_names = _fetch_invoice_names(supabase, invoices)

    return InvoiceListResponse(
        data=[_build_invoice_response(inv, owner_names, pet_names) for inv in invoices],
        total=total,
    )


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_in: InvoiceCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new invoice"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    # Validate owner
    owner_resp = (
        supabase.table("pet_owners")
        .select("id, name")
        .eq("id", invoice_in.owner_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not owner_resp.data:
        raise HTTPException(status_code=404, detail="Owner not found")

    # Validate pet
    pet_resp = (
        supabase.table("pets")
        .select("id, name")
        .eq("id", invoice_in.pet_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not pet_resp.data:
        raise HTTPException(status_code=404, detail="Pet not found")

    # Validate appointment if provided
    if invoice_in.appointment_id:
        appt_resp = (
            supabase.table("appointments")
            .select("id")
            .eq("id", invoice_in.appointment_id)
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .execute()
        )
        if not appt_resp.data:
            raise HTTPException(status_code=404, detail="Appointment not found")

    invoice_number = f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    new_invoice = {
        "clinic_id": clinic_id,
        "invoice_number": invoice_number,
        **invoice_in.model_dump(),
    }
    response = supabase.table("invoices").insert(new_invoice).execute()
    invoice = response.data[0]

    owner_names = {str(owner_resp.data[0]["id"]): owner_resp.data[0]["name"]}
    pet_names = {str(pet_resp.data[0]["id"]): pet_resp.data[0]["name"]}
    return _build_invoice_response(invoice, owner_names, pet_names)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single invoice by ID"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    response = (
        supabase.table("invoices")
        .select("*")
        .eq("id", invoice_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = response.data[0]
    owner_names, pet_names = _fetch_invoice_names(supabase, [invoice])
    return _build_invoice_response(invoice, owner_names, pet_names)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    invoice_in: InvoiceUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing invoice"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("invoices")
        .select("*")
        .eq("id", invoice_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    update_data = invoice_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    response = (
        supabase.table("invoices")
        .update(update_data)
        .eq("id", invoice_id)
        .eq("clinic_id", clinic_id)
        .execute()
    )
    invoice = response.data[0]

    owner_names, pet_names = _fetch_invoice_names(supabase, [invoice])
    return _build_invoice_response(invoice, owner_names, pet_names)


@router.delete("/{invoice_id}", response_model=MessageResponse)
async def delete_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete an invoice"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    existing = (
        supabase.table("invoices")
        .select("id")
        .eq("id", invoice_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    supabase.table("invoices").update(
        {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", invoice_id).eq("clinic_id", clinic_id).execute()

    return MessageResponse(message="Invoice deleted successfully")


@router.post("/{invoice_id}/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    invoice_id: str,
    payment_in: PaymentCreate,
    current_user: dict = Depends(get_current_user),
):
    """Record a payment for an invoice"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    # Validate invoice exists in this clinic
    invoice_resp = (
        supabase.table("invoices")
        .select("id")
        .eq("id", invoice_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not invoice_resp.data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    new_payment = {
        "clinic_id": clinic_id,
        **payment_in.model_dump(),
    }
    response = supabase.table("payments").insert(new_payment).execute()
    payment = response.data[0]

    return PaymentResponse(
        id=str(payment["id"]),
        clinic_id=str(payment["clinic_id"]),
        invoice_id=str(payment["invoice_id"]),
        amount=float(payment["amount"]),
        payment_method=payment["payment_method"],
        payment_date=str(payment["payment_date"]),
        transaction_id=payment.get("transaction_id"),
        notes=payment.get("notes"),
        created_at=str(payment["created_at"]),
        updated_at=str(payment["updated_at"]),
    )


@router.get("/{invoice_id}/payments", response_model=PaymentListResponse)
async def list_payments(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
):
    """List all payments for an invoice"""
    supabase = get_supabase()
    clinic_id = current_user["clinic_id"]

    # Validate invoice exists in this clinic
    invoice_resp = (
        supabase.table("invoices")
        .select("id")
        .eq("id", invoice_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    if not invoice_resp.data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    response = (
        supabase.table("payments")
        .select("*", count="exact")
        .eq("invoice_id", invoice_id)
        .eq("clinic_id", clinic_id)
        .eq("is_deleted", False)
        .execute()
    )
    payments = response.data
    total = response.count or 0

    payment_responses = [
        PaymentResponse(
            id=str(p["id"]),
            clinic_id=str(p["clinic_id"]),
            invoice_id=str(p["invoice_id"]),
            amount=float(p["amount"]),
            payment_method=p["payment_method"],
            payment_date=str(p["payment_date"]),
            transaction_id=p.get("transaction_id"),
            notes=p.get("notes"),
            created_at=str(p["created_at"]),
            updated_at=str(p["updated_at"]),
        )
        for p in payments
    ]

    return PaymentListResponse(data=payment_responses, total=total)
