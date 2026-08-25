from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.deps import get_current_business, get_current_user
from database import get_db
from models import Business, User
from schemas import BillingStatusRead, CheckoutSessionRequest, CheckoutSessionResponse, PortalSessionResponse
from services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["Billing"])


async def get_billing_service(db: AsyncSession = Depends(get_db)) -> BillingService:
    return BillingService(db)


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    data: CheckoutSessionRequest,
    business: Business = Depends(get_current_business),
    user: User = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service),
):
    url = await billing_service.create_checkout_session(business, user.email, data.plan)
    return CheckoutSessionResponse(url=url)


@router.post("/portal-session", response_model=PortalSessionResponse)
async def create_portal_session(
    business: Business = Depends(get_current_business),
    billing_service: BillingService = Depends(get_billing_service),
):
    url = await billing_service.create_portal_session(business)
    return PortalSessionResponse(url=url)


@router.get("/status", response_model=BillingStatusRead)
async def get_billing_status(business: Business = Depends(get_current_business)):
    return BillingStatusRead.model_validate(business)


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, billing_service: BillingService = Depends(get_billing_service)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    await billing_service.handle_webhook_event(payload, sig_header)
    return {"received": True}
