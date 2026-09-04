from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services.auth_service import AuthError, login_user, register_user
from app.core.rate_limit import register_ip_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"


    if await register_ip_limiter.is_limited(client_ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many registration attempts — please wait")

    try:
        user = await register_user(db, body.username, body.email, body.password)
    except AuthError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        token = await login_user(db, body.username, body.password)
    except AuthError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    return TokenResponse(token=token)