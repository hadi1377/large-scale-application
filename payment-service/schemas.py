from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal
import uuid


class PaymentRequest(BaseModel):
    """Schema for payment request with order information"""
    order_id: uuid.UUID = Field(..., description="Order ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount must be greater than 0")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": "99.99"
            }
        }


class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: uuid.UUID
    order_id: uuid.UUID
    amount: Decimal
    status: str
    payment_gateway_charge_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

