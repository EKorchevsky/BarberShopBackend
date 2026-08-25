from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import col
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from enums import UserRole
from models import User, Business, RefreshToken
from schemas import BusinessRegisterRequest, BusinessUpdate
from utils.auth_utils import hash_password, create_tokens


class BusinessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: BusinessRegisterRequest) -> tuple[Business, dict]:
        owner_in = data.owner

        res_email = await self.db.execute(select(User).where(col(User.email) == str(owner_in.email)))
        if res_email.scalars().first():
            raise HTTPException(status_code=400, detail="User with this email already exists")

        res_user = await self.db.execute(select(User).where(col(User.username) == owner_in.username))
        if res_user.scalars().first():
            raise HTTPException(status_code=400, detail="User with this username already exists")

        owner = User(
            username=owner_in.username,
            email=str(owner_in.email),
            password=hash_password(owner_in.password),
            role=UserRole.BarberAdmin,
        )
        self.db.add(owner)
        await self.db.flush()

        business = Business(
            owner_id=owner.id,
            name=data.business.name,
            description=data.business.description,
            address=data.business.address,
        )
        self.db.add(business)
        await self.db.flush()

        token_data = create_tokens(owner)
        rt_db = RefreshToken(
            token=token_data["refresh_token"],
            user_id=owner.id,
            expires_at=token_data["rt_expires_at"]
        )
        self.db.add(rt_db)

        await self.db.commit()
        await self.db.refresh(business)

        return business, token_data

    async def get_my_business(self, user: User) -> Business:
        res = await self.db.execute(select(Business).where(col(Business.owner_id) == user.id))
        business = res.scalars().first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found for this account")
        return business

    async def update_my_business(self, user: User, data: BusinessUpdate) -> Business:
        business = await self.get_my_business(user)
        if data.name is not None:
            business.name = data.name
        if data.description is not None:
            business.description = data.description
        if data.address is not None:
            business.address = data.address
        self.db.add(business)
        await self.db.commit()
        await self.db.refresh(business)
        return business

    async def list_businesses(self, limit: int = 20, offset: int = 0) -> list[Business]:
        res = await self.db.execute(
            select(Business).options(selectinload(Business.barbers)).offset(offset).limit(limit)
        )
        return list(res.scalars().all())

    async def get_business_with_barbers(self, business_id: int) -> Business:
        res = await self.db.execute(
            select(Business).options(selectinload(Business.barbers)).where(col(Business.id) == business_id)
        )
        business = res.scalars().first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        return business
