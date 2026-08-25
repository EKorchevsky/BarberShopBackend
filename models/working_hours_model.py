from typing import Optional, TYPE_CHECKING
from datetime import time

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .barber_model import Barber


class WorkingHours(SQLModel, table=True):
    __tablename__ = "working_hours"
    __allow_unmapped__ = True
    __table_args__ = (UniqueConstraint("barber_id", "day_of_week", name="uq_working_hours_barber_day"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    barber_id: int = Field(foreign_key="barbers.id", ondelete="CASCADE")

    day_of_week: int = Field(ge=0, le=6)  # 0 = Monday ... 6 = Sunday
    start_time: time
    end_time: time
    is_working: bool = Field(default=True)

    barber: "Barber" = Relationship(back_populates="working_hours")
