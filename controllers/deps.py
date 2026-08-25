from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, col

from config import settings
from database import get_db
from enums import UserRole
from models import User, Business, Barber
from services.auth_service import AuthService
from services.business_service import BusinessService
from services.barber_service import BarberService
from services.catalog_service import CatalogService
from services.schedule_service import ScheduleService
from services.appointment_service import AppointmentService
from services.review_service import ReviewService


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_business_service(db: AsyncSession = Depends(get_db)) -> BusinessService:
    return BusinessService(db)


async def get_barber_service(db: AsyncSession = Depends(get_db)) -> BarberService:
    return BarberService(db)


async def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


async def get_schedule_service(db: AsyncSession = Depends(get_db)) -> ScheduleService:
    return ScheduleService(db)


async def get_appointment_service(db: AsyncSession = Depends(get_db)) -> AppointmentService:
    return AppointmentService(db)


async def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    return ReviewService(db)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = str(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    statement = select(User).where(User.id == int(user_id))
    result = await db.execute(statement)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def get_optional_current_user(
        token: str | None = Depends(optional_oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = str(payload.get("sub"))
        if not user_id:
            return None

        statement = select(User).where(User.id == int(user_id))
        result = await db.execute(statement)
        user = result.scalars().first()

        return user
    except (JWTError, ValueError):
        return None


def require_role(*roles: UserRole):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return user
    return checker


async def get_current_business(
    user: User = Depends(require_role(UserRole.BarberAdmin)),
    db: AsyncSession = Depends(get_db),
) -> Business:
    result = await db.execute(select(Business).where(col(Business.owner_id) == user.id))
    business = result.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found for this account")
    return business


async def get_current_barber(
    user: User = Depends(require_role(UserRole.BARBER)),
    db: AsyncSession = Depends(get_db),
) -> Barber:
    result = await db.execute(select(Barber).where(col(Barber.user_id) == user.id))
    barber = result.scalars().first()
    if not barber:
        raise HTTPException(status_code=404, detail="Barber profile not found for this account")
    return barber