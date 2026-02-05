from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProductCreate(BaseModel):
    """Schema for creating a product"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Product price must be greater than 0")
    stock: int = Field(..., ge=0, description="Stock quantity must be non-negative")
    category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional product properties as key-value pairs"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Laptop",
                "description": "High-performance laptop",
                "price": 999.99,
                "stock": 50,
                "category": "Electronics",
                "properties": {
                    "color": "Silver",
                    "brand": "TechCorp",
                    "warranty": "2 years",
                    "weight": "2.5 kg"
                }
            }
        }
    )


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0, description="Product price must be greater than 0")
    stock: Optional[int] = Field(None, ge=0, description="Stock quantity must be non-negative")
    category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional product properties as key-value pairs"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Laptop",
                "description": "Updated description",
                "price": 1099.99,
                "stock": 45,
                "category": "Electronics",
                "properties": {
                    "color": "Black",
                    "brand": "TechCorp",
                    "warranty": "3 years"
                }
            }
        }
    )


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Laptop",
                "description": "High-performance laptop",
                "price": 999.99,
                "stock": 50,
                "category": "Electronics",
                "properties": {
                    "color": "Silver",
                    "brand": "TechCorp",
                    "warranty": "2 years",
                    "weight": "2.5 kg"
                },
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )

