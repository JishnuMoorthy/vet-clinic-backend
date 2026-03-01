"""Authentication routes: login, me, logout"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import create_access_token, get_current_user, verify_password
from app.database import get_supabase
from app.schemas.auth import LoginRequest, MessageResponse, TokenResponse, UserResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate a user and return a JWT access token"""
    supabase = get_supabase()
    response = (
        supabase.table("users")
        .select("*")
        .eq("email", request.email)
        .eq("is_deleted", False)
        .eq("is_active", True)
        .execute()
    )
    users = response.data
    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user = users[0]
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token_data = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "clinic_id": str(user["clinic_id"]),
    }
    access_token = create_access_token(token_data)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile"""
    return UserResponse(
        id=str(current_user["id"]),
        clinic_id=str(current_user["clinic_id"]),
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        phone=current_user.get("phone"),
        is_active=current_user["is_active"],
        created_at=str(current_user["created_at"]),
        specialties=[],
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout the current user (client should discard the token)"""
    return MessageResponse(message="Successfully logged out")
