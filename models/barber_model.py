from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user_model import User
    from .business_model import Business
    from .portfolio_photo_model import PortfolioPhoto
    from .service_model import Service
    from .working_hours_model import WorkingHours
    from .day_off_model import DayOff
    from .appointment_model import Appointment
    from .review_model import Review


class Barber(SQLModel, table=True):
    __tablename__ = "barbers"
    __allow_unmapped__ = True

    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(foreign_key="businesses.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="users.id", unique=True, ondelete="CASCADE")

    display_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    avatar_url: Optional[str] = Field(default=None, max_length=1000)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    business: "Business" = Relationship(back_populates="barbers")
    user: "User" = Relationship()
    portfolio_photos: list["PortfolioPhoto"] = Relationship(back_populates="barber", cascade_delete=True)
    services: list["Service"] = Relationship(back_populates="barber", cascade_delete=True)
    working_hours: list["WorkingHours"] = Relationship(back_populates="barber", cascade_delete=True)
    days_off: list["DayOff"] = Relationship(back_populates="barber", cascade_delete=True)
    appointments: list["Appointment"] = Relationship(back_populates="barber", cascade_delete=True)
    reviews: list["Review"] = Relationship(back_populates="barber", cascade_delete=True)
