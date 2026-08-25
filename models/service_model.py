from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .barber_model import Barber


class Service(SQLModel, table=True):
    __tablename__ = "services"
    __allow_unmapped__ = True

    id: Optional[int] = Field(default=None, primary_key=True)
    barber_id: int = Field(foreign_key="barbers.id", ondelete="CASCADE")

    name: str = Field(max_length=150)
    duration_minutes: int
    price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    barber: "Barber" = Relationship(back_populates="services")
