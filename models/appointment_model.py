from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

from enums import AppointmentStatus

if TYPE_CHECKING:
    from .barber_model import Barber
    from .service_model import Service


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"
    __allow_unmapped__ = True

    id: Optional[int] = Field(default=None, primary_key=True)
    barber_id: int = Field(foreign_key="barbers.id", ondelete="CASCADE")
    service_id: int = Field(foreign_key="services.id", ondelete="CASCADE")

    client_name: str = Field(max_length=100)
    client_email: str = Field(max_length=255)
    client_phone: str = Field(max_length=30)

    start_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    end_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    status: AppointmentStatus = Field(default=AppointmentStatus.CONFIRMED)
    cancel_reason: Optional[str] = Field(default=None, max_length=500)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    barber: "Barber" = Relationship(back_populates="appointments")
    service: "Service" = Relationship()
