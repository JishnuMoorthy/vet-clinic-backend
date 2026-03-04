"""Pydantic schemas for invoices and payments"""
from typing import Optional
from pydantic import BaseModel


class InvoiceCreate(BaseModel):
    owner_id: str
    pet_id: str
    appointment_id: Optional[str] = None
    amount: float
    tax_amount: Optional[float] = 0
    total_amount: float
    due_date: Optional[str] = None
    issue_date: str
    notes: Optional[str] = None
    status: Optional[str] = "pending"


class InvoiceUpdate(BaseModel):
    owner_id: Optional[str] = None
    pet_id: Optional[str] = None
    appointment_id: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    due_date: Optional[str] = None
    issue_date: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: str
    clinic_id: str
    owner_id: str
    pet_id: str
    appointment_id: Optional[str] = None
    invoice_number: str
    amount: float
    tax_amount: Optional[float] = None
    total_amount: float
    status: Optional[str] = None
    due_date: Optional[str] = None
    issue_date: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    owner_name: Optional[str] = None
    pet_name: Optional[str] = None


class InvoiceListResponse(BaseModel):
    data: list[InvoiceResponse]
    total: int


class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    payment_method: str
    payment_date: str
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    clinic_id: str
    invoice_id: str
    amount: float
    payment_method: str
    payment_date: str
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class PaymentListResponse(BaseModel):
    data: list[PaymentResponse]
    total: int
