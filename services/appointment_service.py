from datetime import date as date_type, datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlmodel import col
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException

from enums import AppointmentStatus
from models import Appointment, Barber, Service, WorkingHours, DayOff
from schemas import AppointmentCreate, AvailabilitySlot
from services import notification_service

BUFFER_MINUTES = 10


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_service_with_barber(self, service_id: int) -> tuple[Service, Barber]:
        service = await self.db.get(Service, service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        barber = await self.db.get(Barber, service.barber_id)
        if not barber:
            raise HTTPException(status_code=404, detail="Barber not found")
        return service, barber

    async def _get_working_hours(self, barber_id: int, day_of_week: int) -> Optional[WorkingHours]:
        res = await self.db.execute(
            select(WorkingHours).where(
                col(WorkingHours.barber_id) == barber_id, col(WorkingHours.day_of_week) == day_of_week
            )
        )
        return res.scalars().first()

    async def _is_day_off(self, barber_id: int, day: date_type) -> bool:
        res = await self.db.execute(
            select(DayOff).where(col(DayOff.barber_id) == barber_id, col(DayOff.date) == day)
        )
        return res.scalars().first() is not None

    async def _get_confirmed_appointments(
        self, barber_id: int, window_start: datetime, window_end: datetime
    ) -> list[Appointment]:
        buffer = timedelta(minutes=BUFFER_MINUTES)
        res = await self.db.execute(
            select(Appointment).where(
                col(Appointment.barber_id) == barber_id,
                col(Appointment.status) == AppointmentStatus.CONFIRMED,
                col(Appointment.start_at) < window_end + buffer,
                col(Appointment.end_at) > window_start - buffer,
            )
        )
        return list(res.scalars().all())

    @staticmethod
    def _conflicts(start_at: datetime, end_at: datetime, existing: list[Appointment]) -> bool:
        buffer = timedelta(minutes=BUFFER_MINUTES)
        return any(start_at < a.end_at + buffer and end_at > a.start_at - buffer for a in existing)

    async def compute_availability(self, barber_id: int, service_id: int, day: date_type) -> list[AvailabilitySlot]:
        service, barber = await self._get_service_with_barber(service_id)
        if barber.id != barber_id:
            raise HTTPException(status_code=400, detail="Service does not belong to this barber")

        if await self._is_day_off(barber_id, day):
            return []

        working_hours = await self._get_working_hours(barber_id, day.weekday())
        if not working_hours or not working_hours.is_working:
            return []

        tz = timezone.utc
        day_start = datetime.combine(day, time.min, tzinfo=tz)
        day_end = datetime.combine(day, time.max, tzinfo=tz)
        existing = await self._get_confirmed_appointments(barber_id, day_start, day_end)

        duration = timedelta(minutes=service.duration_minutes)
        cursor = datetime.combine(day, working_hours.start_time, tzinfo=tz)
        work_end = datetime.combine(day, working_hours.end_time, tzinfo=tz)
        now = datetime.now(tz)

        slots: list[AvailabilitySlot] = []
        while cursor + duration <= work_end:
            slot_end = cursor + duration
            if cursor > now and not self._conflicts(cursor, slot_end, existing):
                slots.append(AvailabilitySlot(start_at=cursor, end_at=slot_end))
            cursor += duration

        return slots

    async def create_appointment(
            self,
            data: AppointmentCreate,
            background_tasks: BackgroundTasks,
    ) -> Appointment:

        service, barber = await self._get_service_with_barber(data.service_id)

        start_at = data.start_at

        if start_at.tzinfo is None:
            start_at = start_at.replace(tzinfo=timezone.utc)

        end_at = start_at + timedelta(
            minutes=service.duration_minutes + BUFFER_MINUTES
        )

        if start_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Cannot book a slot in the past",
            )

        if await self._is_day_off(barber.id, start_at.date()):
            raise HTTPException(
                status_code=400,
                detail="Barber is not working on this day",
            )

        working_hours = await self._get_working_hours(
            barber.id,
            start_at.weekday(),
        )

        if not working_hours or not working_hours.is_working:
            raise HTTPException(
                status_code=400,
                detail="Barber is not working on this day",
            )

        if (
                start_at.time() < working_hours.start_time
                or end_at.time() > working_hours.end_time
        ):
            raise HTTPException(
                status_code=400,
                detail="Selected time is outside working hours",
            )

        overlapping = await self._get_confirmed_appointments(
            barber.id,
            start_at,
            end_at,
        )

        if self._conflicts(start_at, end_at, overlapping):
            raise HTTPException(
                status_code=409,
                detail="This time slot is already booked",
            )

        appointment = Appointment(
            barber_id=barber.id,
            service_id=service.id,
            client_name=data.client_name,
            client_email=str(data.client_email),
            client_phone=data.client_phone,
            start_at=start_at,
            end_at=end_at,
            status=AppointmentStatus.CONFIRMED,
        )

        self.db.add(appointment)

        try:
            await self.db.commit()

        except IntegrityError:
            await self.db.rollback()

            raise HTTPException(
                status_code=409,
                detail="This time slot was booked by another client",
            )

        await self.db.refresh(appointment)

        background_tasks.add_task(
            notification_service.send_appointment_confirmation,
            appointment,
            service,
            barber,
        )

        return appointment

    async def list_my_appointments(
        self,
        barber: Barber,
        date_from: Optional[date_type],
        date_to: Optional[date_type],
        status: Optional[AppointmentStatus],
    ) -> list[Appointment]:
        stmt = select(Appointment).where(col(Appointment.barber_id) == barber.id)
        if date_from:
            stmt = stmt.where(col(Appointment.start_at) >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
        if date_to:
            stmt = stmt.where(col(Appointment.start_at) <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
        if status:
            stmt = stmt.where(col(Appointment.status) == status)
        stmt = stmt.order_by(col(Appointment.start_at))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_owned_appointment(self, barber: Barber, appointment_id: int) -> Appointment:
        res = await self.db.execute(
            select(Appointment).where(
                col(Appointment.id) == appointment_id, col(Appointment.barber_id) == barber.id
            )
        )
        appointment = res.scalars().first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appointment

    async def cancel_appointment(
        self, barber: Barber, appointment_id: int, reason: Optional[str], background_tasks: BackgroundTasks
    ) -> Appointment:
        appointment = await self.get_owned_appointment(barber, appointment_id)
        if appointment.status == AppointmentStatus.CANCELLED:
            return appointment

        service = await self.db.get(Service, appointment.service_id)
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancel_reason = reason
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)

        background_tasks.add_task(
            notification_service.send_appointment_cancellation, appointment, service, barber, reason
        )
        return appointment

    async def cancel_confirmed_for_day(
        self, barber: Barber, day: date_type, reason: Optional[str], background_tasks: BackgroundTasks
    ) -> list[Appointment]:
        day_start = datetime.combine(day, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(day, time.max, tzinfo=timezone.utc)
        appointments = await self._get_confirmed_appointments(barber.id, day_start, day_end)

        cancel_reason = reason or "The barber marked this day as a day off"
        for appointment in appointments:
            service = await self.db.get(Service, appointment.service_id)
            appointment.status = AppointmentStatus.CANCELLED
            appointment.cancel_reason = cancel_reason
            self.db.add(appointment)
            background_tasks.add_task(
                notification_service.send_appointment_cancellation, appointment, service, barber, cancel_reason
            )

        if appointments:
            await self.db.commit()
            for appointment in appointments:
                await self.db.refresh(appointment)

        return appointments
