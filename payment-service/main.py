from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from database import engine, Base, get_db
from models import Payment
from schemas import PaymentRequest, PaymentResponse

app = FastAPI(title="Payment Service")


@app.on_event("startup")
async def startup():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def root():
    return {"service": "payment-service"}


@app.get("/orders/{order_id}/payments", response_model=List[PaymentResponse])
async def get_order_payments(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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

