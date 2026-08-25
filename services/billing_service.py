from datetime import datetime, timezone

import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from config import settings
from models import Business

stripe.api_key = settings.STRIPE_SECRET_KEY

_ACTIVE_STATUSES = {"trialing", "active", "past_due"}

_PLAN_PRICE_IDS = {
    "monthly": settings.STRIPE_PRICE_MONTHLY,
    "yearly": settings.STRIPE_PRICE_YEARLY,
}
_PRICE_ID_PLANS = {v: k for k, v in _PLAN_PRICE_IDS.items() if v}


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_checkout_session(self, business: Business, email: str, plan: str) -> str:
        price_id = _PLAN_PRICE_IDS.get(plan)
        if not price_id:
            raise HTTPException(status_code=400, detail="Unknown plan")

        if business.subscription_status in _ACTIVE_STATUSES:
            raise HTTPException(status_code=400, detail="This business already has a subscription")

        if not business.stripe_customer_id:
            customer = stripe.Customer.create(email=email, name=business.name, metadata={"business_id": business.id})
            business.stripe_customer_id = customer.id
            self.db.add(business)
            await self.db.commit()
            await self.db.refresh(business)

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=business.stripe_customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            subscription_data={"trial_period_days": settings.STRIPE_TRIAL_DAYS},
            payment_method_collection="always",
            success_url=f"{settings.FRONTEND_URL}/dashboard/business/billing?status=success",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard/business/billing?status=cancel",
            client_reference_id=str(business.id),
        )
        return session.url

    async def create_portal_session(self, business: Business) -> str:
        if not business.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No billing account for this business yet")
        session = stripe.billing_portal.Session.create(
            customer=business.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/dashboard/business/billing",
        )
        return session.url

    async def handle_webhook_event(self, payload: bytes, sig_header: str) -> None:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.SignatureVerificationError):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        event_type = event["type"]
        data = event["data"]["object"].to_dict()

        if event_type == "checkout.session.completed":
            subscription_id = data.get("subscription")
            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id).to_dict()
                await self._sync_from_subscription(subscription)
        elif event_type in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
            await self._sync_from_subscription(data)

    async def _sync_from_subscription(self, subscription: dict) -> None:
        customer_id = subscription.get("customer")
        res = await self.db.execute(select(Business).where(col(Business.stripe_customer_id) == customer_id))
        business = res.scalars().first()
        if not business:
            return

        business.stripe_subscription_id = subscription.get("id")
        business.subscription_status = subscription.get("status")

        trial_end = subscription.get("trial_end")
        business.trial_ends_at = datetime.fromtimestamp(trial_end, tz=timezone.utc) if trial_end else None

        period_end = subscription.get("current_period_end")
        business.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None

        items = (subscription.get("items") or {}).get("data") or []
        if items:
            price_id = (items[0].get("price") or {}).get("id")
            business.subscription_plan = _PRICE_ID_PLANS.get(price_id, business.subscription_plan)

        self.db.add(business)
        await self.db.commit()
