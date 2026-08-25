from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .barber_model import Barber


class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    __allow_unmapped__ = True
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    barber_id: int = Field(foreign_key="barbers.id", ondelete="CASCADE")

    author_name: str = Field(max_length=100)
    rating: int
    comment: Optional[str] = Field(default=None, max_length=2000)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    barber: "Barber" = Relationship(back_populates="reviews")
