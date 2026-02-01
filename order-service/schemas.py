from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field
from decimal import Decimal
import uuid


class OrderItemCreate(BaseModel):
    """Schema for creating an order item"""
    product_id: str = Field(..., description="Product ID from product service")
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "507f1f77bcf86cd799439011",
                "quantity": 2
            }
        }


class OrderCreate(BaseModel):
    """Schema for creating an order"""
    items: List[OrderItemCreate] = Field(..., min_items=1, description="At least one item is required")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 2
                    },
                    {
                        "product_id": "507f1f77bcf86cd799439012",
                        "quantity": 1
                    }
                ]
            }
        }


class OrderItemResponse(BaseModel):
    """Schema for order item response"""
    id: uuid.UUID
    order_id: uuid.UUID
    product_id: str
    quantity: int
    price_per_item: Decimal

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    """Schema for updating an order status"""
    status: Literal["completed", "failed"] = Field(..., description="Order status: 'completed' or 'failed'")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed"
            }
        }


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

