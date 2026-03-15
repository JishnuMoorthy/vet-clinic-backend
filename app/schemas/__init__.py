"""Schemas package for request/response models"""
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, MessageResponse, LoginResponse
from app.schemas.owners import OwnerCreate, OwnerUpdate, OwnerResponse, OwnerListResponse
from app.schemas.pets import PetCreate, PetUpdate, PetResponse, PetListResponse
from app.schemas.staff import StaffCreate, StaffUpdate, StaffResponse, StaffListResponse
from app.schemas.appointments import AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentListResponse
from app.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse, InventoryListResponse
from app.schemas.invoices import InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse, PaymentCreate, PaymentResponse, PaymentListResponse
from app.schemas.dashboard import DashboardStats
