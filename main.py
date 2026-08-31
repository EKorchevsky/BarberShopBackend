import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from controllers import (
    auth_router,
    business_router,
    barber_router,
    catalog_router,
    schedule_router,
    appointment_router,
    review_router,
    billing_router,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Barbershop SaaS Backend",
    description="Backend for barbershop management: businesses, barbers, services, bookings, reviews"
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://barber-shop-frontend-delta.vercel.app/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(business_router)
app.include_router(barber_router)
app.include_router(catalog_router)
app.include_router(schedule_router)
app.include_router(appointment_router)
app.include_router(review_router)
app.include_router(billing_router)

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "message": "Service is running"}
