from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

BillingPlan = Literal["monthly", "yearly"]


class CheckoutSessionRequest(BaseModel):
    plan: BillingPlan


class CheckoutSessionResponse(BaseModel):
    url: str


class PortalSessionResponse(BaseModel):
    url: str


class BillingStatusRead(BaseModel):
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    current_period_end: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
