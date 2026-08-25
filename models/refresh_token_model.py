from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import Relationship, Field, SQLModel

from models import User


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    __allow_unmapped__ = True

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True)

    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE")

    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    user: User = Relationship(back_populates="refresh_tokens")