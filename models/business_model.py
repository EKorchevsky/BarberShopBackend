from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user_model import User
    from .barber_model import Barber


class Business(SQLModel, table=True):
    __tablename__ = "businesses"
    __allow_unmapped__ = True

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", unique=True, ondelete="CASCADE")

    name: str = Field(max_length=150)
    description: Optional[str] = Field(default=None, max_length=2000)
    address: Optional[str] = Field(default=None, max_length=255)

    stripe_customer_id: Optional[str] = Field(default=None, max_length=255, index=True)
    stripe_subscription_id: Optional[str] = Field(default=None, max_length=255)
    subscription_status: Optional[str] = Field(default=None, max_length=30)
    subscription_plan: Optional[str] = Field(default=None, max_length=20)
    trial_ends_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    current_period_end: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    owner: "User" = Relationship()
    barbers: list["Barber"] = Relationship(back_populates="business", cascade_delete=True)
