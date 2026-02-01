from fastapi import FastAPI, HTTPException, status, Query
from typing import List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

from database import connect_to_mongo, close_mongo_connection, get_database
from schemas import ProductCreate, ProductUpdate, ProductResponse

app = FastAPI(
    title="Product Service",
    description="Product management service with CRUD operations",
    version="1.0.0"
)


@app.on_event("startup")
async def startup():
    """Initialize database connection on startup"""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown"""
    await close_mongo_connection()


@app.get("/")
def root():
    return {"service": "product-service"}


def product_to_dict(product: dict) -> dict:
    """Convert MongoDB document to response format"""
    product["id"] = str(product["_id"])
    product.pop("_id", None)
    return product


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate):
    """
    Create a new product.
    
    - **name**: Product name (required, 1-200 characters)
    - **description**: Product description (optional)
    - **price**: Product price (required, must be > 0)
    - **stock**: Stock quantity (required, must be >= 0)
    - **category**: Product category (optional)
    - **properties**: Additional product properties as key-value pairs (optional)
    """
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    collection = db.products
    
    # Create product document
    product_dict = product.dict()
    product_dict["created_at"] = datetime.utcnow()
    product_dict["updated_at"] = datetime.utcnow()
    
    # Insert product
    result = await collection.insert_one(product_dict)
    
    # Retrieve the created product
    created_product = await collection.find_one({"_id": result.inserted_id})
    
    if not created_product:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )
    
    return product_to_dict(created_product)


@app.get("/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter")
):
    """
    Get a list of products with optional filtering and pagination.
    
    - **skip**: Number of products to skip (for pagination)
    - **limit**: Number of products to return (1-100)
    - **category**: Filter products by category
    - **min_price**: Filter products with price >= min_price
    - **max_price**: Filter products with price <= max_price
    """
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    collection = db.products
    
    # Build filter query
    filter_query = {}
    if category:
        filter_query["category"] = category
    if min_price is not None or max_price is not None:
        filter_query["price"] = {}
        if min_price is not None:
            filter_query["price"]["$gte"] = min_price
        if max_price is not None:
            filter_query["price"]["$lte"] = max_price
    
    # Fetch products
    cursor = collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
    products = await cursor.to_list(length=limit)
    
    return [product_to_dict(product) for product in products]


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """
    Get a single product by ID.
    
    - **product_id**: The unique identifier of the product
    """
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    # Validate ObjectId
    try:
        object_id = ObjectId(product_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    collection = db.products
    product = await collection.find_one({"_id": object_id})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    return product_to_dict(product)


@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product_update: ProductUpdate):
    """
    Update a product by ID.
    
    - **product_id**: The unique identifier of the product
    - **product_update**: Fields to update (all fields are optional)
        - **name**: Product name (optional)
        - **description**: Product description (optional)
        - **price**: Product price (optional, must be > 0)
        - **stock**: Stock quantity (optional, must be >= 0)
        - **category**: Product category (optional)
        - **properties**: Product properties as key-value pairs (optional, replaces existing properties)
    """
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    # Validate ObjectId
    try:
        object_id = ObjectId(product_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    collection = db.products
    
    # Check if product exists
    existing_product = await collection.find_one({"_id": object_id})
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Prepare update data (only include fields that are provided)
    update_data = {k: v for k, v in product_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Add updated_at timestamp
    update_data["updated_at"] = datetime.utcnow()
    
    # Update product
    await collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
    )
    
    # Retrieve updated product
    updated_product = await collection.find_one({"_id": object_id})
    
    return product_to_dict(updated_product)


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str):
    """
    Delete a product by ID.
    
    - **product_id**: The unique identifier of the product
    """
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    # Validate ObjectId
    try:
        object_id = ObjectId(product_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )
    
    collection = db.products
    
    # Check if product exists and delete
    result = await collection.delete_one({"_id": object_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    return None

