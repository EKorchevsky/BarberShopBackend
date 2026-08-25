from fastapi import APIRouter, Depends, File, UploadFile, status

from controllers.deps import get_barber_service, get_current_barber, get_current_business
from models import Barber, Business
from schemas import BarberCreate, BarberUpdate, BarberRead, BarberDetail, PortfolioPhotoRead
from services.barber_service import BarberService
from services.storage_service import upload_file, delete_file

router = APIRouter(prefix="/barbers", tags=["Barbers"])


@router.post("", response_model=BarberRead, status_code=status.HTTP_201_CREATED)
async def create_barber(
    data: BarberCreate,
    business: Business = Depends(get_current_business),
    barber_service: BarberService = Depends(get_barber_service),
):
    return await barber_service.create_barber(business, data)


@router.delete("/{barber_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_barber(
    barber_id: int,
    business: Business = Depends(get_current_business),
    barber_service: BarberService = Depends(get_barber_service),
):
    await barber_service.delete_barber(business, barber_id)


@router.get("/me", response_model=BarberRead)
async def get_my_profile(
    barber: Barber = Depends(get_current_barber),
):
    return barber


@router.patch("/me", response_model=BarberRead)
async def update_my_profile(
    data: BarberUpdate,
    barber: Barber = Depends(get_current_barber),
    barber_service: BarberService = Depends(get_barber_service),
):
    return await barber_service.update_profile(barber, data)


@router.post("/me/avatar", response_model=BarberRead)
async def upload_avatar(
    file: UploadFile = File(...),
    barber: Barber = Depends(get_current_barber),
    barber_service: BarberService = Depends(get_barber_service),
):
    url = await upload_file(file, prefix=f"barbers/{barber.id}/avatar")
    return await barber_service.set_avatar(barber, url)


@router.post("/me/portfolio", response_model=PortfolioPhotoRead, status_code=status.HTTP_201_CREATED)
async def upload_portfolio_photo(
    file: UploadFile = File(...),
    barber: Barber = Depends(get_current_barber),
    barber_service: BarberService = Depends(get_barber_service),
):
    url = await upload_file(file, prefix=f"barbers/{barber.id}/portfolio")
    return await barber_service.add_portfolio_photo(barber, url)


@router.delete("/me/portfolio/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_photo(
    photo_id: int,
    barber: Barber = Depends(get_current_barber),
    barber_service: BarberService = Depends(get_barber_service),
):
    photo = await barber_service.get_owned_portfolio_photo(barber, photo_id)
    await barber_service.delete_portfolio_photo(photo)
    await delete_file(photo.url)


@router.get("/{barber_id}", response_model=BarberDetail)
async def get_barber(
    barber_id: int,
    barber_service: BarberService = Depends(get_barber_service),
):
    return await barber_service.get_barber_detail(barber_id)
