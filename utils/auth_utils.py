import uuid

from passlib.context import CryptContext
import jwt
from authlib.jose import jwt
from datetime import datetime, timedelta, timezone
from starlette.responses import Response
from config import settings
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_tokens(user: User):
    now = datetime.now(timezone.utc)
    header = {'alg': settings.ALGORITHM}

    rt_expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    rt_expires_at = now + rt_expires_delta

    access_payload = {
        'sub': str(user.id),
        'username': str(user.username),
        'role': user.role.value,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
    }

    refresh_payload = {
        'sub': str(user.id),
        'iat': int(now.timestamp()),
        'exp': int(rt_expires_at.timestamp()),
        "jti": str(uuid.uuid4())
    }

    at = jwt.encode(header, access_payload, settings.SECRET_KEY).decode('utf-8')
    rt = jwt.encode(header, refresh_payload, settings.SECRET_KEY).decode('utf-8')

    return {
        "access_token": at,
        "refresh_token": rt,
        "rt_expires_at": rt_expires_at
    }


def decode_token(token: str):
    claims = jwt.decode(token, settings.SECRET_KEY)
    claims.validate()
    return claims


def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.IS_PRODUCTION,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth/refresh"
    )