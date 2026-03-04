"""Pydantic schemas for dashboard statistics"""
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_pets: int
    total_owners: int
    total_appointments: int
    upcoming_appointments: int
    total_staff: int
    total_inventory_items: int
    low_stock_items: int
    pending_invoices: int
    total_revenue: float
