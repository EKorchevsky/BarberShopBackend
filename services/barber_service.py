from datetime import time
from typing import Optional

from sqlalchemy import select, func
from sqlmodel import col
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from enums import UserRole
from models import User, Business, Barber, PortfolioPhoto, Review, WorkingHours
from schemas import BarberCreate, BarberUpdate, BarberPublic, BarberDetail, BarberRead
from utils.auth_utils import hash_password

DEFAULT_WORKDAY_START = time(9, 0)
DEFAULT_WORKDAY_END = time(18, 0)


class BarberService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_barber(self, business: Business, data: BarberCreate) -> Barber:
        res_email = await self.db.execute(select(User).where(col(User.email) == str(data.email)))
        if res_email.scalars().first():
            raise HTTPException(status_code=400, detail="User with this email already exists")

        res_user = await self.db.execute(select(User).where(col(User.username) == data.username))
        if res_user.scalars().first():
            raise HTTPException(status_code=400, detail="User with this username already exists")

        user = User(
            username=data.username,
            email=str(data.email),
            password=hash_password(data.password),
            role=UserRole.BARBER,
        )
        self.db.add(user)
        await self.db.flush()

        barber = Barber(
            business_id=business.id,
            user_id=user.id,
            display_name=data.display_name,
            description=data.description,
        )
        self.db.add(barber)
        await self.db.flush()

        for day in range(7):
            self.db.add(WorkingHours(
                barber_id=barber.id,
                day_of_week=day,
                start_time=DEFAULT_WORKDAY_START,
                end_time=DEFAULT_WORKDAY_END,
                is_working=day < 5,
            ))

        await self.db.commit()
        await self.db.refresh(barber)
        return barber

    async def get_owned_barber(self, business: Business, barber_id: int) -> Barber:
        res = await self.db.execute(
            select(Barber).where(col(Barber.id) == barber_id, col(Barber.business_id) == business.id)
        )
        barber = res.scalars().first()
        if not barber:
            raise HTTPException(status_code=404, detail="Barber not found")
        return barber

    async def delete_barber(self, business: Business, barber_id: int) -> None:
        barber = await self.get_owned_barber(business, barber_id)
        user = await self.db.get(User, barber.user_id)
        await self.db.delete(barber)
        if user:
            await self.db.delete(user)
        await self.db.commit()

    async def update_profile(self, barber: Barber, data: BarberUpdate) -> Barber:
        if data.display_name is not None:
            barber.display_name = data.display_name
        if data.description is not None:
            barber.description = data.description
        self.db.add(barber)
        await self.db.commit()
        await self.db.refresh(barber)
        return barber

    async def set_avatar(self, barber: Barber, url: str) -> Barber:
        barber.avatar_url = url
        self.db.add(barber)
        await self.db.commit()
        await self.db.refresh(barber)
        return barber

    async def add_portfolio_photo(self, barber: Barber, url: str) -> PortfolioPhoto:
        photo = PortfolioPhoto(barber_id=barber.id, url=url)
        self.db.add(photo)
        await self.db.commit()
        await self.db.refresh(photo)
        return photo

    async def get_owned_portfolio_photo(self, barber: Barber, photo_id: int) -> PortfolioPhoto:
        res = await self.db.execute(
            select(PortfolioPhoto).where(
                col(PortfolioPhoto.id) == photo_id, col(PortfolioPhoto.barber_id) == barber.id
            )
        )
        photo = res.scalars().first()
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        return photo

    async def delete_portfolio_photo(self, photo: PortfolioPhoto) -> None:
        await self.db.delete(photo)
        await self.db.commit()

    async def get_rating_summary(self, barber_id: int) -> tuple[Optional[float], int]:
        res = await self.db.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(col(Review.barber_id) == barber_id)
        )
        avg, count = res.one()
        return (round(float(avg), 2) if avg is not None else None, count or 0)

    async def to_public(self, barber: Barber) -> BarberPublic:
        avg, count = await self.get_rating_summary(barber.id)
        return BarberPublic(**BarberRead.model_validate(barber).model_dump(), average_rating=avg, review_count=count)

    async def get_barber_detail(self, barber_id: int) -> BarberDetail:
        res = await self.db.execute(
            select(Barber)
            .options(
                selectinload(Barber.services),
                selectinload(Barber.portfolio_photos),
                selectinload(Barber.reviews),
            )
            .where(col(Barber.id) == barber_id)
        )
        barber = res.scalars().first()
        if not barber:
            raise HTTPException(status_code=404, detail="Barber not found")

        avg, count = await self.get_rating_summary(barber.id)
        return BarberDetail(
            **BarberRead.model_validate(barber).model_dump(),
            average_rating=avg,
            review_count=count,
            services=barber.services,
            portfolio_photos=barber.portfolio_photos,
            reviews=sorted(barber.reviews, key=lambda r: r.created_at, reverse=True),
        )
