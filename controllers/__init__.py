from .v1.auth_controller import router as auth_router
from .v1.business_controller import router as business_router
from .v1.barber_controller import router as barber_router
from .v1.catalog_controller import router as catalog_router
from .v1.schedule_controller import router as schedule_router
from .v1.appointment_controller import router as appointment_router
from .v1.review_controller import router as review_router
from .v1.billing_controller import router as billing_router

__all__ = [
    "auth_router",
    "business_router",
    "barber_router",
    "catalog_router",
    "schedule_router",
    "appointment_router",
    "review_router",
    "billing_router",
]
