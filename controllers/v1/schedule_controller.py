from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, status

from controllers.deps import get_current_barber, get_schedule_service
from models import Barber
from schemas import WorkingHoursBulkUpdate, WorkingHoursRead, DayOffCreate, DayOffRead
from services.schedule_service import ScheduleService

router = APIRouter(prefix="/barbers/me", tags=["Schedule"])


@router.get("/working-hours", response_model=list[WorkingHoursRead])
async def get_working_hours(
    barber: Barber = Depends(get_current_barber),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    return await schedule_service.get_working_hours(barber)


@router.put("/working-hours", response_model=list[WorkingHoursRead])
async def set_working_hours(
    data: WorkingHoursBulkUpdate,
    barber: Barber = Depends(get_current_barber),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    return await schedule_service.set_working_hours(barber, data)


@router.get("/days-off", response_model=list[DayOffRead])
async def list_days_off(
    barber: Barber = Depends(get_current_barber),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    return await schedule_service.list_days_off(barber)


@router.post("/days-off", response_model=DayOffRead, status_code=status.HTTP_201_CREATED)
async def add_day_off(
    data: DayOffCreate,
    background_tasks: BackgroundTasks,
    barber: Barber = Depends(get_current_barber),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    return await schedule_service.add_day_off(barber, data, background_tasks)


@router.delete("/days-off/{day}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_day_off(
    day: date,
    barber: Barber = Depends(get_current_barber),
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    await schedule_service.remove_day_off(barber, day)
