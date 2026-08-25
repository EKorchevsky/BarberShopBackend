from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from schemas.service_schema import ServiceRead
from schemas.review_schema import ReviewRead


class BarberCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)


class BarberUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)


class PortfolioPhotoRead(BaseModel):
    id: int
    url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BarberRead(BaseModel):
    id: int
    business_id: int
    display_name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BarberPublic(BarberRead):
    average_rating: Optional[float] = None
    review_count: int = 0


class BarberDetail(BarberPublic):
    services: list[ServiceRead] = []
    portfolio_photos: list[PortfolioPhotoRead] = []
    reviews: list[ReviewRead] = []
