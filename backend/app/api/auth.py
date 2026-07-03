from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token
from app.api.deps import current_user
from app.db.mongo import get_db
from app.db.repositories import UserRepository
from app.models.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    user = await UserRepository(get_db()).authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user["username"], user["role"], user["_id"]),
        role=user["role"],
        user=user,
    )


@router.get("/auth/me", response_model=UserOut)
async def me(user: dict = Depends(current_user)):
    return user
