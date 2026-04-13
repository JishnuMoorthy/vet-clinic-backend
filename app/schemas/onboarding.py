"""Schemas for clinic onboarding."""
from pydantic import BaseModel, EmailStr


class ClinicOnboardRequest(BaseModel):
    clinic_name: str
    clinic_phone: str
    admin_name: str
    admin_email: EmailStr
    admin_password: str
    include_demo_data: bool = True


class ClinicOnboardResponse(BaseModel):
    message: str
    clinic: dict
    admin: dict
