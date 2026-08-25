from fastapi import APIRouter, Depends, status

from controllers.deps import get_catalog_service, get_current_barber
from models import Barber
from schemas import ServiceCreate, ServiceUpdate, ServiceRead
from services.catalog_service import CatalogService

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: ServiceCreate,
    barber: Barber = Depends(get_current_barber),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    return await catalog_service.create_service(barber, data)


@router.get("/me", response_model=list[ServiceRead])
async def list_my_services(
    barber: Barber = Depends(get_current_barber),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    return await catalog_service.list_my_services(barber)


@router.patch("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: int,
    data: ServiceUpdate,
    barber: Barber = Depends(get_current_barber),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    return await catalog_service.update_service(barber, service_id, data)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    barber: Barber = Depends(get_current_barber),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    await catalog_service.delete_service(barber, service_id)
