from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from enums import AppointmentStatus


class AppointmentCreate(BaseModel):
    service_id: int
    start_at: datetime
    client_name: str = Field(max_length=100)
    client_email: EmailStr
    client_phone: str = Field(max_length=30)


class AppointmentCancel(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


class AppointmentRead(BaseModel):
    id: int
    barber_id: int
    service_id: int
    client_name: str
    client_email: str
    client_phone: str
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    cancel_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailabilitySlot(BaseModel):
    start_at: datetime
    end_at: datetime
