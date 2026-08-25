from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, status

from controllers.deps import get_current_user, get_review_service
from models import User
from schemas import ReviewCreate, ReviewRead
from services.review_service import ReviewService
from utils.review_cookie import can_review_barber

router = APIRouter(tags=["Reviews"])


@router.get("/barbers/{barber_id}/reviews", response_model=list[ReviewRead])
async def list_reviews(
    barber_id: int,
    limit: int = 20,
    offset: int = 0,
    review_service: ReviewService = Depends(get_review_service),
):
    return await review_service.list_reviews(barber_id, limit=limit, offset=offset)


@router.post("/barbers/{barber_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    barber_id: int,
    data: ReviewCreate,
    reviewable_barbers: Optional[str] = Cookie(default=None),
    review_service: ReviewService = Depends(get_review_service),
):
    if not can_review_barber(reviewable_barbers, barber_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients who booked an appointment with this barber can leave a review"
        )
    return await review_service.create_review(barber_id, data)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    await review_service.delete_review_as_owner(user.id, review_id)
