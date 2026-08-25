from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkingHoursItem(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_working: bool = True

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: time, info):
        start = info.data.get("start_time")
        if start is not None and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class WorkingHoursBulkUpdate(BaseModel):
    items: list[WorkingHoursItem]

    @field_validator("items")
    @classmethod
    def unique_days(cls, v: list[WorkingHoursItem]):
        days = [item.day_of_week for item in v]
        if len(days) != len(set(days)):
            raise ValueError("duplicate day_of_week in working hours")
        return v


class WorkingHoursRead(WorkingHoursItem):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DayOffCreate(BaseModel):
    date: date
    reason: Optional[str] = Field(default=None, max_length=500)


class DayOffRead(BaseModel):
    id: int
    date: date
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
