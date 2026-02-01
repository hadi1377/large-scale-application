from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import httpx
from typing import List

from database import engine, Base, get_db
from models import Order, OrderItem
from schemas import OrderCreate, OrderResponse, OrderItemResponse
from auth import verify_token

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(
    title="Order Service",
    description="Order management service with order creation and processing",
    version="1.0.0"
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token (from /login endpoint in user-service)"
        }
    }
    
    # Add security requirement to /orders endpoints
    if "paths" in openapi_schema and "/orders" in openapi_schema["paths"]:
        if "post" in openapi_schema["paths"]["/orders"]:
            openapi_schema["paths"]["/orders"]["post"]["security"] = [{"Bearer": []}]
        if "get" in openapi_schema["paths"]["/orders"]:
            openapi_schema["paths"]["/orders"]["get"]["security"] = [{"Bearer": []}]
    
    # Add security requirement to /orders/{order_id} endpoint
    if "paths" in openapi_schema and "/orders/{order_id}" in openapi_schema["paths"]:
        if "get" in openapi_schema["paths"]["/orders/{order_id}"]:
            openapi_schema["paths"]["/orders/{order_id}"]["get"]["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Service URLs
PRODUCT_SERVICE_URL = "http://product-service:8000"
USER_SERVICE_URL = "http://user-service:8000"


@app.on_event("startup")
async def startup():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def root():
    return {"service": "order-service"}


async def get_current_user_id(
    token: str = Depends(oauth2_scheme)
) -> str:
    """Get the current authenticated user ID from the JWT token."""
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_info(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """Get the current authenticated user ID and role by validating token with user-service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Call user-service /me endpoint to validate token and get user info
            response = await client.get(
                f"{USER_SERVICE_URL}/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="User service is unavailable"
                )
            
            user_data = response.json()
            user_id = str(user_data.get("id"))
            role = user_data.get("main_role", "user")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user data",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return {"user_id": user_id, "role": role}
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Timeout connecting to user service"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to user service"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating token: {str(e)}"
        )


async def verify_products_and_stock(items: List[dict]) -> dict:
    """
    Verify that all products exist and have sufficient stock.
    Returns a dictionary mapping product_id to product data.
    """
    product_data = {}
    errors = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            try:
                # Fetch product from product service
                response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
                
                if response.status_code == 404:
                    errors.append(f"Product with ID {product_id} not found")
                    continue
                elif response.status_code != 200:
                    errors.append(f"Error fetching product {product_id}: HTTP {response.status_code}")
                    continue
                
                product = response.json()
                product_data[product_id] = product
                
                # Check stock availability
                if product.get("stock", 0) < quantity:
                    errors.append(
                        f"Product {product.get('name', product_id)} has insufficient stock. "
                        f"Available: {product.get('stock', 0)}, Requested: {quantity}"
                    )
                
            except httpx.TimeoutException:
                errors.append(f"Timeout while fetching product {product_id}")
            except httpx.ConnectError:
                errors.append("Cannot connect to product service")
            except Exception as e:
                errors.append(f"Error verifying product {product_id}: {str(e)}")
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Product validation failed",
                "errors": errors
            }
        )
    
    return product_data


@app.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(oauth2_scheme)]
)
async def create_order(
    order_data: OrderCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new order.
    
    - **items**: List of order items, each containing:
        - **product_id**: Product ID from product service
        - **quantity**: Quantity to order (must be > 0)
    
    Prices are automatically fetched from the product service.
    Requires authentication via JWT token.
    Validates that all products exist and have sufficient stock.
    
    **How to use:**
    1. Login using `/login` endpoint in user-service to get your access token
    2. Click the "Authorize" button at the top of this page
    3. Enter your token (just the token, without "Bearer" prefix)
    4. Click "Authorize" and then "Close"
    5. Now you can use the "Try it out" button on this endpoint
    """
    # Prepare items for validation
    items_for_validation = [
        {
            "product_id": item.product_id,
            "quantity": item.quantity
        }
        for item in order_data.items
    ]
    
    # Verify products exist and have sufficient stock
    # This also fetches product data including prices
    product_data = await verify_products_and_stock(items_for_validation)
    
    # Calculate total amount using prices from product service
    total_amount = Decimal("0.00")
    for item in order_data.items:
        product = product_data[item.product_id]
        product_price = Decimal(str(product["price"]))
        item_total = product_price * item.quantity
        total_amount += item_total
    
    # Create order
    import uuid as uuid_lib
    order = Order(
        user_id=uuid_lib.UUID(user_id),
        status="pending",
        total_amount=total_amount
    )
    
    # Fix: Create order first, then add items
    db.add(order)
    await db.flush()  # Flush to get the order ID
    
    # Create order items using prices from product service
    order_items = []
    for item in order_data.items:
        product = product_data[item.product_id]
        product_price = Decimal(str(product["price"]))
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_per_item=product_price
        )
        db.add(order_item)
        order_items.append(order_item)
    
    await db.commit()
    await db.refresh(order)
    
    # Refresh order items
    for item in order_items:
        await db.refresh(item)
    
    # Build response
    order_response = OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_per_item=item.price_per_item
            )
            for item in order_items
        ]
    )
    
    return order_response


async def build_order_response(order: Order, db: AsyncSession) -> OrderResponse:
    """Helper function to build OrderResponse with items."""
    # Fetch order items
    result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    order_items = result.scalars().all()
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_per_item=item.price_per_item
            )
            for item in order_items
        ]
    )


@app.get(
    "/orders",
    response_model=List[OrderResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(oauth2_scheme)]
)
async def list_orders(
    user_info: dict = Depends(get_current_user_info),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """
    Get a list of orders.
    
    - **Admin users**: Can see all orders
    - **Regular users**: Can only see their own orders
    
    - **skip**: Number of orders to skip (for pagination)
    - **limit**: Number of orders to return (default: 10, max: 100)
    
    Requires authentication via JWT token.
    """
    user_id = user_info["user_id"]
    role = user_info["role"]
    
    # Limit the maximum number of results
    limit = min(limit, 100)
    
    import uuid as uuid_lib
    
    # Build query based on user role
    if role == "admin":
        # Admin can see all orders
        query = select(Order).order_by(Order.created_at.desc())
    else:
        # Regular users can only see their own orders
        query = select(Order).where(
            Order.user_id == uuid_lib.UUID(user_id)
        ).order_by(Order.created_at.desc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # Build responses with items
    order_responses = []
    for order in orders:
        order_response = await build_order_response(order, db)
        order_responses.append(order_response)
    
    return order_responses


@app.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(oauth2_scheme)]
)
async def get_order(
    order_id: str,
    user_info: dict = Depends(get_current_user_info),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single order by ID.
    
    - **Admin users**: Can see any order
    - **Regular users**: Can only see their own orders
    
    Requires authentication via JWT token.
    """
    user_id = user_info["user_id"]
    role = user_info["role"]
    
    import uuid as uuid_lib
    
    # Validate order_id format
    try:
        order_uuid = uuid_lib.UUID(order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )
    
    # Fetch order
    result = await db.execute(
        select(Order).where(Order.id == order_uuid)
    )
    order = result.scalar_one_or_none()
    
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    
    # Check access permission
    if role != "admin" and order.user_id != uuid_lib.UUID(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this order"
        )
    
    # Build and return response
    return await build_order_response(order, db)
