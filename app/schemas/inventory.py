"""Pydantic schemas for inventory"""
from typing import Optional
from pydantic import BaseModel


class InventoryCreate(BaseModel):
    item_name: str
    item_type: Optional[str] = None
    quantity: int
    unit: Optional[str] = None
    low_stock_threshold: Optional[int] = 10
    supplier: Optional[str] = None
    cost_per_unit: Optional[float] = None
    last_restocked_date: Optional[str] = None


class InventoryUpdate(BaseModel):
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    low_stock_threshold: Optional[int] = None
    supplier: Optional[str] = None
    cost_per_unit: Optional[float] = None
    last_restocked_date: Optional[str] = None


class InventoryResponse(BaseModel):
    id: str
    clinic_id: str
    item_name: str
    item_type: Optional[str] = None
    quantity: int
    unit: Optional[str] = None
    low_stock_threshold: Optional[int] = None
    supplier: Optional[str] = None
    cost_per_unit: Optional[float] = None
    last_restocked_date: Optional[str] = None
    created_at: str
    updated_at: str
    is_low_stock: Optional[bool] = False


class InventoryListResponse(BaseModel):
    data: list[InventoryResponse]
    total: int
