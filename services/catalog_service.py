from sqlalchemy import select
from sqlmodel import col
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from models import Barber, Service
from schemas import ServiceCreate, ServiceUpdate


class CatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_service(self, barber: Barber, data: ServiceCreate) -> Service:
        service = Service(
            barber_id=barber.id,
            name=data.name,
            duration_minutes=data.duration_minutes,
            price=data.price,
        )
        self.db.add(service)
        await self.db.commit()
        await self.db.refresh(service)
        return service

    async def list_my_services(self, barber: Barber) -> list[Service]:
        res = await self.db.execute(select(Service).where(col(Service.barber_id) == barber.id))
        return list(res.scalars().all())

    async def get_owned_service(self, barber: Barber, service_id: int) -> Service:
        res = await self.db.execute(
            select(Service).where(col(Service.id) == service_id, col(Service.barber_id) == barber.id)
        )
        service = res.scalars().first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service

    async def update_service(self, barber: Barber, service_id: int, data: ServiceUpdate) -> Service:
        service = await self.get_owned_service(barber, service_id)
        if data.name is not None:
            service.name = data.name
        if data.duration_minutes is not None:
            service.duration_minutes = data.duration_minutes
        if data.price is not None:
            service.price = data.price
        self.db.add(service)
        await self.db.commit()
        await self.db.refresh(service)
        return service

    async def delete_service(self, barber: Barber, service_id: int) -> None:
        service = await self.get_owned_service(barber, service_id)
        await self.db.delete(service)
        await self.db.commit()
