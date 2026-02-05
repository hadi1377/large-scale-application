from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from contextlib import asynccontextmanager
import uuid
import os
from database import engine, Base, get_db
from models import Payment
from schemas import PaymentRequest, PaymentResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown (no cleanup needed)


app = FastAPI(title="Payment Service", lifespan=lifespan)

# API Key for service-to-service authentication
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "order-service-secret-key-2024")


async def verify_service_api_key(
    x_service_api_key: Optional[str] = Header(None, alias="X-Service-API-Key")
):
    """
    Verify that the request comes from an authorized service (order-service).
    Only requests with the correct API key are allowed.
    """
    if x_service_api_key != SERVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Invalid or missing service API key."
        )
    return True


@app.get("/")
def root():
    return {"service": "payment-service"}


@app.get("/orders/{order_id}/payments", response_model=List[PaymentResponse])
async def get_order_payments(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_api_key)
):
    """
    Get all payments for a specific order.
    
    - **order_id**: UUID of the order to get payments for
    
    Returns a list of all payment records associated with the order.
    """
    result = await db.execute(
        select(Payment).where(Payment.order_id == order_id)
    )
    payments = result.scalars().all()
    return payments


@app.post("/success", response_model=PaymentResponse)
async def payment_success(
    payment_data: PaymentRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_api_key)
):
    """
    Handle successful payment callback.
    Creates or updates payment record with status 'success'.
    """
    # Check if payment already exists for this order
    result = await db.execute(
        select(Payment).where(Payment.order_id == payment_data.order_id)
    )
    existing_payment = result.scalar_one_or_none()
    
    if existing_payment:
        # Update existing payment
        existing_payment.status = "success"
        existing_payment.amount = payment_data.amount
        await db.commit()
        await db.refresh(existing_payment)
        return existing_payment
    else:
        # Create new payment record
        new_payment = Payment(
            order_id=payment_data.order_id,
            amount=payment_data.amount,
            status="success",
            payment_gateway_charge_id="paypal"
        )
        db.add(new_payment)
        await db.commit()
        await db.refresh(new_payment)
        return new_payment


@app.post("/failed", response_model=PaymentResponse)
async def payment_failed(
    payment_data: PaymentRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_api_key)
):
    """
    Handle failed payment callback.
    Creates or updates payment record with status 'failed'.
    """
    # Check if payment already exists for this order
    result = await db.execute(
        select(Payment).where(Payment.order_id == payment_data.order_id)
    )
    existing_payment = result.scalar_one_or_none()
    
    if existing_payment:
        # Update existing payment
        existing_payment.status = "failed"
        existing_payment.amount = payment_data.amount
        await db.commit()
        await db.refresh(existing_payment)
        return existing_payment
    else:
        # Create new payment record
        new_payment = Payment(
            order_id=payment_data.order_id,
            amount=payment_data.amount,
            status="failed",
            payment_gateway_charge_id="paypal"
        )
        db.add(new_payment)
        await db.commit()
        await db.refresh(new_payment)
        return new_payment

