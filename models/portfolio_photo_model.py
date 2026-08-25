from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .barber_model import Barber


class PortfolioPhoto(SQLModel, table=True):
    __tablename__ = "portfolio_photos"
    __allow_unmapped__ = True

    id: Optional[int] = Field(default=None, primary_key=True)
    barber_id: int = Field(foreign_key="barbers.id", ondelete="CASCADE")

    url: str = Field(max_length=1000)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    barber: "Barber" = Relationship(back_populates="portfolio_photos")
