from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException
from datetime import datetime, timezone

from sqlmodel import col

from config import settings
from models import User, RefreshToken
from schemas import UserCreate
from utils.auth_utils import hash_password, verify_password, create_tokens, decode_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_in: UserCreate):
        res_email = await self.db.execute(select(User).where(col(User.email) == str(user_in.email)))
        if res_email.scalars().first():
            raise HTTPException(status_code=400, detail="User with this email already exists")

        res_user = await self.db.execute(select(User).where(col(User.username) == str(user_in.username)))
        if res_user.scalars().first():
            raise HTTPException(status_code=400, detail="User with this username already exists")

        new_user = User(
            username=user_in.username,
            email=str(user_in.email),
            password=hash_password(user_in.password)
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def login(self, username, password):
        res = await self.db.execute(select(User).where(col(User.username) == username))
        user = res.scalars().first()

        if not user or not verify_password(password, str(user.password)):
            raise HTTPException(status_code=401, detail="Bad credentials")

        token_data = create_tokens(user)

        rt_db = RefreshToken(
            token=token_data["refresh_token"],
            user_id=user.id,
            expires_at=token_data["rt_expires_at"]
        )
        self.db.add(rt_db)
        await self.db.commit()

        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    async def refresh_access_token(self, refresh_token: str):
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = payload.get("sub")

        # Use a transaction so this stays atomic
        async with self.db.begin_nested():  # Create a savepoint
            res = await self.db.execute(
                select(RefreshToken).where(
                    col(RefreshToken.token) == refresh_token,
                    col(RefreshToken.user_id) == int(user_id)
                )
            )
            db_token = res.scalars().first()

            if not db_token or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="Token revoked or expired")

            user_res = await self.db.execute(select(User).where(col(User.id) == int(user_id)))
            user = user_res.scalars().first()

            # Remove the old one
            await self.db.delete(db_token)

            token_data = create_tokens(user)
            new_db_token = RefreshToken(
                token=token_data["refresh_token"],
                user_id=user.id,
                expires_at=token_data["rt_expires_at"]
            )

            try:
                self.db.add(new_db_token)
                await self.db.flush()
            except IntegrityError:
                await self.db.rollback()
                raise HTTPException(status_code=409, detail="Concurrent refresh request")

        await self.db.commit()

        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    async def logout(self, refresh_token: str):
        await self.db.execute(delete(RefreshToken).where(col(RefreshToken.token) == refresh_token))
        await self.db.commit()
        return {"detail": "Successfully logged out"}