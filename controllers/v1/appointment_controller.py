from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, status
from starlette.responses import Response

from controllers.deps import get_appointment_service, get_current_barber
from enums import AppointmentStatus
from models import Barber
from schemas import AppointmentCreate, AppointmentCancel, AppointmentRead, AvailabilitySlot
from services.appointment_service import AppointmentService
from utils.review_cookie import REVIEW_COOKIE_NAME, REVIEW_COOKIE_MAX_AGE, add_barber_to_cookie

router = APIRouter(tags=["Appointments"])


@router.get("/barbers/{barber_id}/availability", response_model=list[AvailabilitySlot])
async def get_availability(
    barber_id: int,
    service_id: int,
    day: date,
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    return await appointment_service.compute_availability(barber_id, service_id, day)


@router.post("/appointments", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    response: Response,
    reviewable_barbers: Optional[str] = Cookie(default=None),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    appointment = await appointment_service.create_appointment(data, background_tasks)

    new_cookie = add_barber_to_cookie(reviewable_barbers, appointment.barber_id)
    response.set_cookie(
        key=REVIEW_COOKIE_NAME,
        value=new_cookie,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=REVIEW_COOKIE_MAX_AGE,
    )

    return appointment


@router.get("/barbers/me/appointments", response_model=list[AppointmentRead])
async def list_my_appointments(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[AppointmentStatus] = None,
    barber: Barber = Depends(get_current_barber),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    return await appointment_service.list_my_appointments(barber, date_from, date_to, status)


@router.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentRead)
async def cancel_appointment(
    appointment_id: int,
    data: AppointmentCancel,
    background_tasks: BackgroundTasks,
    barber: Barber = Depends(get_current_barber),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    return await appointment_service.cancel_appointment(barber, appointment_id, data.reason, background_tasks)
