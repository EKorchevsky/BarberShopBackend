from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from schemas.barber_schema import BarberPublic


class OwnerCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class BusinessInfo(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None


class BusinessRegisterRequest(BaseModel):
    owner: OwnerCreate
    business: BusinessInfo


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None


class BusinessRead(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusinessWithBarbers(BusinessRead):
    barbers: list[BarberPublic] = []


class BusinessRegisterResponse(BaseModel):
    business: BusinessRead
    access_token: str
    expires_in: int
    token_type: str = "bearer"
