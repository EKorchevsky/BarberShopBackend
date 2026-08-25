from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from config import settings
from controllers.deps import get_business_service, get_current_business, get_current_user
from database import get_db
from models import User
from schemas import (
    BusinessRegisterRequest,
    BusinessRegisterResponse,
    BusinessUpdate,
    BusinessRead,
    BusinessWithBarbers,
)
from services.business_service import BusinessService
from services.barber_service import BarberService
from utils.auth_utils import set_refresh_cookie

router = APIRouter(tags=["Business"])


async def _to_business_with_barbers(business, barber_service: BarberService) -> BusinessWithBarbers:
    barbers_public = [await barber_service.to_public(b) for b in business.barbers]
    return BusinessWithBarbers(
        id=business.id,
        owner_id=business.owner_id,
        name=business.name,
        description=business.description,
        address=business.address,
        created_at=business.created_at,
        barbers=barbers_public,
    )


@router.post("/business/register", response_model=BusinessRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_business(
    data: BusinessRegisterRequest,
    response: Response,
    business_service: BusinessService = Depends(get_business_service),
):
    business, tokens = await business_service.register(data)

    set_refresh_cookie(response, tokens["refresh_token"])

    return BusinessRegisterResponse(
        business=BusinessRead.model_validate(business),
        access_token=tokens["access_token"],
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/business/me", response_model=BusinessRead)
async def get_my_business(
    business=Depends(get_current_business),
):
    return business


@router.patch("/business/me", response_model=BusinessRead)
async def update_my_business(
    data: BusinessUpdate,
    user: User = Depends(get_current_user),
    business_service: BusinessService = Depends(get_business_service),
):
    return await business_service.update_my_business(user, data)


@router.get("/businesses", response_model=list[BusinessWithBarbers])
async def list_businesses(
    limit: int = 20,
    offset: int = 0,
    business_service: BusinessService = Depends(get_business_service),
    db: AsyncSession = Depends(get_db),
):
    businesses = await business_service.list_businesses(limit=limit, offset=offset)
    barber_service = BarberService(db)
    return [await _to_business_with_barbers(business, barber_service) for business in businesses]


@router.get("/businesses/{business_id}", response_model=BusinessWithBarbers)
async def get_business(
    business_id: int,
    business_service: BusinessService = Depends(get_business_service),
    db: AsyncSession = Depends(get_db),
):
    business = await business_service.get_business_with_barbers(business_id)
    barber_service = BarberService(db)
    return await _to_business_with_barbers(business, barber_service)
