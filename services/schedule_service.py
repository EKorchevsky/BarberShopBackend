from datetime import date as date_type

from sqlalchemy import select, delete
from sqlmodel import col
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException

from models import Barber, WorkingHours, DayOff
from schemas import WorkingHoursBulkUpdate, DayOffCreate
from services.appointment_service import AppointmentService


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.appointment_service = AppointmentService(db)

    async def get_working_hours(self, barber: Barber) -> list[WorkingHours]:
        res = await self.db.execute(
            select(WorkingHours).where(col(WorkingHours.barber_id) == barber.id).order_by(col(WorkingHours.day_of_week))
        )
        return list(res.scalars().all())

    async def set_working_hours(self, barber: Barber, data: WorkingHoursBulkUpdate) -> list[WorkingHours]:
        await self.db.execute(delete(WorkingHours).where(col(WorkingHours.barber_id) == barber.id))
        for item in data.items:
            self.db.add(WorkingHours(
                barber_id=barber.id,
                day_of_week=item.day_of_week,
                start_time=item.start_time,
                end_time=item.end_time,
                is_working=item.is_working,
            ))
        await self.db.commit()
        return await self.get_working_hours(barber)

    async def list_days_off(self, barber: Barber) -> list[DayOff]:
        res = await self.db.execute(
            select(DayOff).where(col(DayOff.barber_id) == barber.id).order_by(col(DayOff.date))
        )
        return list(res.scalars().all())

    async def add_day_off(
        self, barber: Barber, data: DayOffCreate, background_tasks: BackgroundTasks
    ) -> DayOff:
        res = await self.db.execute(
            select(DayOff).where(col(DayOff.barber_id) == barber.id, col(DayOff.date) == data.date)
        )
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="This day is already marked as a day off")

        day_off = DayOff(barber_id=barber.id, date=data.date, reason=data.reason)
        self.db.add(day_off)
        await self.db.commit()
        await self.db.refresh(day_off)

        await self.appointment_service.cancel_confirmed_for_day(barber, data.date, data.reason, background_tasks)

        return day_off

    async def remove_day_off(self, barber: Barber, day: date_type) -> None:
        res = await self.db.execute(
            select(DayOff).where(col(DayOff.barber_id) == barber.id, col(DayOff.date) == day)
        )
        day_off = res.scalars().first()
        if not day_off:
            raise HTTPException(status_code=404, detail="Day off not found")
        await self.db.delete(day_off)
        await self.db.commit()
