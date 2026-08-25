from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str = Field(max_length=150)
    duration_minutes: int = Field(gt=0, le=24 * 60)
    price: Decimal = Field(ge=0)


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=150)
    duration_minutes: Optional[int] = Field(default=None, gt=0, le=24 * 60)
    price: Optional[Decimal] = Field(default=None, ge=0)


class ServiceRead(BaseModel):
    id: int
    barber_id: int
    name: str
    duration_minutes: int
    price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
