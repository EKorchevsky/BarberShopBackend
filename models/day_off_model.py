from typing import Optional, TYPE_CHECKING
from datetime import date as date_type, datetime, timezone

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .barber_model import Barber


class DayOff(SQLModel, table=True):
    __tablename__ = "days_off"
    __allow_unmapped__ = True
    __table_args__ = (UniqueConstraint("barber_id", "date", name="uq_day_off_barber_date"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    barber_id: int = Field(foreign_key="barbers.id", ondelete="CASCADE")

    date: date_type
    reason: Optional[str] = Field(default=None, max_length=500)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    barber: "Barber" = Relationship(back_populates="days_off")
