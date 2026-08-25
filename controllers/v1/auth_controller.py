from fastapi import APIRouter, Depends, HTTPException, Cookie, status
from starlette.responses import Response

from controllers.deps import get_auth_service
from schemas import UserRead, UserCreate
from schemas.auth_schema import LoginRequest
from services.auth_service import AuthService
from utils.auth_utils import set_refresh_cookie

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.register(user_data)

@router.post("/login")
async def login(
    login_data: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.login(login_data.username, login_data.password)

    set_refresh_cookie(response, tokens["refresh_token"])

    return {
        "access_token": tokens["access_token"],
        "expires_in": tokens["expires_in"],
        "token_type": "bearer"
    }

@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    new_tokens = await auth_service.refresh_access_token(refresh_token)

    set_refresh_cookie(response, new_tokens["refresh_token"])

    return {
        "access_token": new_tokens["access_token"],
        "expires_in": new_tokens["expires_in"],
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service)
):
    if refresh_token:
        await auth_service.logout(refresh_token)

    response.delete_cookie(key="refresh_token", path="/auth/refresh")

    return {"detail": "Successfully logged out"}