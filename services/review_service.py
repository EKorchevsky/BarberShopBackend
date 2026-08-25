from sqlalchemy import select
from sqlmodel import col
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from models import Barber, Business, Review
from schemas import ReviewCreate


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review(self, barber_id: int, data: ReviewCreate) -> Review:
        barber = await self.db.get(Barber, barber_id)
        if not barber:
            raise HTTPException(status_code=404, detail="Barber not found")

        review = Review(
            barber_id=barber_id,
            author_name=data.author_name,
            rating=data.rating,
            comment=data.comment,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def list_reviews(self, barber_id: int, limit: int = 20, offset: int = 0) -> list[Review]:
        res = await self.db.execute(
            select(Review)
            .where(col(Review.barber_id) == barber_id)
            .order_by(col(Review.created_at).desc())
            .offset(offset)
            .limit(limit)
        )
        return list(res.scalars().all())

    async def delete_review_as_owner(self, owner_user_id: int, review_id: int) -> None:
        res = await self.db.execute(
            select(Review)
            .join(Barber, col(Barber.id) == col(Review.barber_id))
            .join(Business, col(Business.id) == col(Barber.business_id))
            .where(col(Review.id) == review_id, col(Business.owner_id) == owner_user_id)
        )
        review = res.scalars().first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        await self.db.delete(review)
        await self.db.commit()
