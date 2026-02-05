import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from decimal import Decimal
from datetime import datetime, timezone
import httpx

from main import app
from database import Base, get_db
from models import Order, OrderItem
from auth import verify_token

# Helper function to create access tokens for testing
def create_access_token(data: dict):
    """Create a JWT access token for testing."""
    import os
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days
    
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Test database setup - use file-based SQLite so data persists across connections
import tempfile
import os
import atexit

_test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
_test_db_file.close()
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_test_db_file.name}"

# Clean up test database file on exit
def cleanup_test_db():
    try:
        if os.path.exists(_test_db_file.name):
            os.unlink(_test_db_file.name)
    except Exception:
        pass

atexit.register(cleanup_test_db)

# Convert UUID columns to String for SQLite compatibility
from database import Base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import TypeDecorator, String

class GUID(TypeDecorator):
    """A type that stores UUID as string in SQLite"""
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(String(36))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        # Convert UUID to string
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value) if value else None
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)

# Convert all UUID columns to GUID (which becomes String for SQLite)
for table in Base.metadata.tables.values():
    for column in table.columns:
        if isinstance(column.type, PG_UUID):
            # Replace UUID with GUID
            column.type = GUID()
            # Update default to return string
            if column.default is not None:
                if hasattr(column.default, 'arg'):
                    if callable(column.default.arg) and column.default.arg == uuid.uuid4:
                        column.default.arg = lambda: str(uuid.uuid4())
                    elif isinstance(column.default.arg, uuid.UUID):
                        column.default.arg = str(column.default.arg)
                elif callable(column.default):
                    original_default = column.default
                    column.default = lambda: str(original_default())

engine = create_async_engine(TEST_DATABASE_URL, echo=False)

# Register UUID adapter for SQLite
import sqlite3

def adapt_uuid(uuid_obj):
    """Convert UUID to string for SQLite"""
    return str(uuid_obj)

sqlite3.register_adapter(uuid.UUID, adapt_uuid)

from sqlalchemy import event

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set up SQLite connection"""
    # Enable foreign keys
    dbapi_conn.execute("PRAGMA foreign_keys=ON")
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return uuid.uuid4()


@pytest.fixture
def test_token(test_user_id):
    """Create a test JWT token"""
    return create_access_token(data={"sub": str(test_user_id), "email": "test@example.com", "role": "user"})


@pytest.fixture
def admin_token():
    """Create an admin JWT token"""
    admin_id = uuid.uuid4()
    return create_access_token(data={"sub": str(admin_id), "email": "admin@example.com", "role": "admin"})


@pytest.fixture
def mock_product_response():
    """Mock product service response"""
    return {
        "id": "507f1f77bcf86cd799439011",
        "name": "Test Product",
        "price": 99.99,
        "stock": 100,
        "description": "Test Description"
    }


@pytest.fixture
def mock_user_response():
    """Mock user service response"""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "main_role": "user"
    }


@pytest_asyncio.fixture
async def test_order(test_user_id):
    """Create a test order"""
    import asyncio
    
    async def _create_order():
        # Ensure tables exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        order_id = str(uuid.uuid4())
        user_id_str = str(test_user_id)
        
        async with TestingSessionLocal() as session:
            order = Order(
                id=order_id,  # Use string for SQLite compatibility
                user_id=user_id_str,  # Use string for SQLite compatibility
                status="pending",
                total_amount=Decimal("99.99"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
            # Ensure ID is string for consistency
            order.id = str(order.id) if order.id else order_id
            order.user_id = str(order.user_id) if order.user_id else user_id_str
            return order
    
    # Create order and return it
    return await _create_order()


@pytest.mark.asyncio
class TestCreateOrder:
    """Test order creation"""
    
    @patch('main.publish_event')
    @patch('main.call_payment_service')
    @patch('main.call_product_service')
    async def test_create_order_success(
        self, 
        mock_product_service, 
        mock_payment_service, 
        mock_publish,
        client, 
        test_token, 
        test_user_id,
        mock_product_response
    ):
        """Test successful order creation"""
        # Mock product service response
        mock_product_response_obj = MagicMock()
        mock_product_response_obj.status_code = 200
        mock_product_response_obj.json.return_value = mock_product_response
        mock_product_service.return_value = mock_product_response_obj
        
        # Mock payment service response
        mock_payment_response_obj = MagicMock()
        mock_payment_response_obj.status_code = 200
        mock_payment_service.return_value = mock_payment_response_obj
        
        # Mock event publishing
        mock_publish.return_value = True
        
        response = client.post(
            "/orders",
            json={
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 1
                    }
                ],
                "success": True
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["user_id"] == str(test_user_id)
        assert len(data["items"]) == 1
        assert Decimal(str(data["total_amount"])) == Decimal("99.99")
    
    @patch('main.call_product_service')
    async def test_create_order_product_not_found(
        self,
        mock_product_service,
        client,
        test_token
    ):
        """Test order creation with non-existent product"""
        # Mock product service 404 response
        mock_product_response_obj = MagicMock()
        mock_product_response_obj.status_code = 404
        mock_product_service.return_value = mock_product_response_obj
        
        response = client.post(
            "/orders",
            json={
                "items": [
                    {
                        "product_id": "nonexistent",
                        "quantity": 1
                    }
                ],
                "success": True
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 400
    
    @patch('main.call_product_service')
    async def test_create_order_insufficient_stock(
        self,
        mock_product_service,
        client,
        test_token,
        mock_product_response
    ):
        """Test order creation with insufficient stock"""
        # Mock product with low stock
        mock_product_response["stock"] = 5
        
        mock_product_response_obj = MagicMock()
        mock_product_response_obj.status_code = 200
        mock_product_response_obj.json.return_value = mock_product_response
        mock_product_service.return_value = mock_product_response_obj
        
        response = client.post(
            "/orders",
            json={
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 10  # More than available stock
                    }
                ],
                "success": True
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 400
        assert "insufficient stock" in response.json()["detail"]["errors"][0].lower()
    
    @patch('main.call_payment_service')
    @patch('main.call_product_service')
    async def test_create_order_payment_failed(
        self,
        mock_product_service,
        mock_payment_service,
        client,
        test_token,
        mock_product_response
    ):
        """Test order creation with payment failure"""
        # Mock product service response
        mock_product_response_obj = MagicMock()
        mock_product_response_obj.status_code = 200
        mock_product_response_obj.json.return_value = mock_product_response
        mock_product_service.return_value = mock_product_response_obj
        
        # Mock payment service response (payment failed)
        mock_payment_response_obj = MagicMock()
        mock_payment_response_obj.status_code = 200
        mock_payment_service.return_value = mock_payment_response_obj
        
        response = client.post(
            "/orders",
            json={
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 1
                    }
                ],
                "success": False  # Payment will fail
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 402
        assert "payment failed" in response.json()["detail"].lower()
    
    async def test_create_order_invalid_token(self, client):
        """Test order creation with invalid token"""
        response = client.post(
            "/orders",
            json={
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 1
                    }
                ]
            },
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    async def test_create_order_empty_items(self, client, test_token):
        """Test order creation with empty items"""
        response = client.post(
            "/orders",
            json={
                "items": []
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 422
    
    async def test_create_order_invalid_quantity(self, client, test_token):
        """Test order creation with invalid quantity"""
        response = client.post(
            "/orders",
            json={
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 0  # Invalid quantity
                    }
                ]
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListOrders:
    """Test listing orders"""
    
    @patch('main.call_user_service')
    async def test_list_orders_user_success(
        self,
        mock_user_service,
        client,
        test_token,
        test_user_id,
        test_order,
        mock_user_response
    ):
        """Test listing orders for regular user"""
        # Mock user service response
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = mock_user_response
        mock_user_service.return_value = mock_user_response_obj
        
        response = client.get(
            "/orders",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # User should see their own orders
        assert all(order["user_id"] == str(test_user_id) for order in data)
    
    @patch('main.call_user_service')
    async def test_list_orders_admin_success(
        self,
        mock_user_service,
        client,
        admin_token,
        test_order,
        mock_user_response
    ):
        """Test listing orders for admin"""
        # Mock admin user response
        admin_response = {**mock_user_response, "main_role": "admin"}
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = admin_response
        mock_user_service.return_value = mock_user_response_obj
        
        response = client.get(
            "/orders",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Admin can see all orders
    
    @patch('main.call_user_service')
    async def test_list_orders_with_pagination(
        self,
        mock_user_service,
        client,
        test_token,
        mock_user_response
    ):
        """Test listing orders with pagination"""
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = mock_user_response
        mock_user_service.return_value = mock_user_response_obj
        
        response = client.get(
            "/orders?skip=0&limit=5",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 200
    
    async def test_list_orders_invalid_token(self, client):
        """Test listing orders with invalid token"""
        response = client.get(
            "/orders",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetOrder:
    """Test getting single order"""
    
    @patch('main.call_user_service')
    async def test_get_order_success(
        self,
        mock_user_service,
        client,
        test_token,
        test_user_id,
        test_order,
        mock_user_response
    ):
        """Test getting order by ID"""
        # Update mock_user_response to use the same user_id as test_user_id
        mock_user_response_with_correct_id = {
            **mock_user_response,
            "id": str(test_user_id)
        }
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = mock_user_response_with_correct_id
        mock_user_service.return_value = mock_user_response_obj
        
        response = client.get(
            f"/orders/{test_order.id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_order.id)
        assert data["user_id"] == str(test_user_id)
    
    @patch('main.call_user_service')
    async def test_get_order_not_found(
        self,
        mock_user_service,
        client,
        test_token,
        mock_user_response
    ):
        """Test getting non-existent order"""
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = mock_user_response
        mock_user_service.return_value = mock_user_response_obj
        
        fake_id = uuid.uuid4()
        response = client.get(
            f"/orders/{fake_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 404
    
    @patch('main.call_user_service')
    async def test_get_order_unauthorized(
        self,
        mock_user_service,
        client,
        test_token,
        mock_user_response
    ):
        """Test getting order from different user"""
        # Create order for different user
        other_user_id = uuid.uuid4()
        async with TestingSessionLocal() as session:
            other_order = Order(
                id=uuid.uuid4(),
                user_id=other_user_id,
                status="pending",
                total_amount=Decimal("99.99"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(other_order)
            await session.commit()
            await session.refresh(other_order)
        
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = mock_user_response
        mock_user_service.return_value = mock_user_response_obj
        
        response = client.get(
            f"/orders/{other_order.id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 403
    
    @patch('main.call_user_service')
    async def test_get_order_invalid_id(
        self,
        mock_user_service,
        client,
        test_token,
        mock_user_response
    ):
        """Test getting order with invalid ID format"""
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = mock_user_response
        mock_user_service.return_value = mock_user_response_obj
        
        response = client.get(
            "/orders/invalid-id",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestUpdateOrder:
    """Test updating order"""
    
    @patch('main.publish_event')
    @patch('main.call_user_service')
    async def test_update_order_success(
        self,
        mock_user_service,
        mock_publish,
        client,
        admin_token,
        test_order,
        mock_user_response
    ):
        """Test successful order update by admin"""
        admin_response = {**mock_user_response, "main_role": "admin"}
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = admin_response
        mock_user_service.return_value = mock_user_response_obj
        
        mock_publish.return_value = True
        
        response = client.put(
            f"/orders/{test_order.id}",
            json={
                "status": "completed"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
    
    @patch('main.call_user_service')
    async def test_update_order_non_admin(
        self,
        mock_user_service,
        client,
        test_token,
        test_order,
        mock_user_response
    ):
        """Test order update by non-admin user"""
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = mock_user_response
        mock_user_service.return_value = mock_user_response_obj
        
        response = client.put(
            f"/orders/{test_order.id}",
            json={
                "status": "completed"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 403
    
    @patch('main.call_user_service')
    async def test_update_order_invalid_status(
        self,
        mock_user_service,
        client,
        admin_token,
        test_order,
        mock_user_response
    ):
        """Test order update with invalid status"""
        admin_response = {**mock_user_response, "main_role": "admin"}
        mock_user_response_obj = MagicMock()
        mock_user_response_obj.status_code = 200
        mock_user_response_obj.json.return_value = admin_response
        mock_user_service.return_value = mock_user_response_obj
        
        response = client.put(
            f"/orders/{test_order.id}",
            json={
                "status": "invalid_status"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test root endpoint"""
    
    async def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"service": "order-service"}


@pytest.mark.asyncio
class TestCircuitBreakerHealth:
    """Test circuit breaker health endpoint"""
    
    async def test_circuit_breaker_health(self, client):
        """Test circuit breaker health check"""
        response = client.get("/health/circuit-breakers")
        assert response.status_code == 200
        data = response.json()
        assert "user_service" in data
        assert "product_service" in data
        assert "payment_service" in data

