import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
import tempfile
import os
import atexit
from decimal import Decimal
from datetime import datetime, timezone

from main import app
from database import Base, get_db
from models import Payment

# Test database setup - use file-based SQLite so data persists across connections
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
    # Ensure tables exist (don't drop, just create if needed)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """Get valid API key from environment or default"""
    import os
    return os.getenv("SERVICE_API_KEY", "order-service-secret-key-2024")


@pytest_asyncio.fixture
async def test_payment():
    """Create a test payment"""
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    payment_id = str(uuid.uuid4())
    order_id = str(uuid.uuid4())
    
    async with TestingSessionLocal() as session:
        payment = Payment(
            id=payment_id,  # Use string for SQLite compatibility
            order_id=order_id,  # Use string for SQLite compatibility
            amount=Decimal("99.99"),
            status="success",
            payment_gateway_charge_id="paypal",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        # Ensure IDs are strings for consistency
        payment.id = str(payment.id) if payment.id else payment_id
        payment.order_id = str(payment.order_id) if payment.order_id else order_id
        return payment


@pytest.mark.asyncio
class TestPaymentSuccess:
    """Test payment success endpoint"""
    
    async def test_payment_success_new(self, client, valid_api_key):
        """Test successful payment creation"""
        order_id = uuid.uuid4()
        response = client.post(
            "/success",
            json={
                "order_id": str(order_id),
                "amount": "99.99"
            },
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["order_id"] == str(order_id)
        assert Decimal(str(data["amount"])) == Decimal("99.99")
    
    async def test_payment_success_update_existing(self, client, valid_api_key, test_payment):
        """Test updating existing payment to success"""
        response = client.post(
            "/success",
            json={
                "order_id": str(test_payment.order_id),
                "amount": "149.99"
            },
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert Decimal(str(data["amount"])) == Decimal("149.99")
    
    async def test_payment_success_invalid_api_key(self, client):
        """Test payment success with invalid API key"""
        response = client.post(
            "/success",
            json={
                "order_id": str(uuid.uuid4()),
                "amount": "99.99"
            },
            headers={"X-Service-API-Key": "invalid-key"}
        )
        assert response.status_code == 403
    
    async def test_payment_success_missing_api_key(self, client):
        """Test payment success without API key"""
        response = client.post(
            "/success",
            json={
                "order_id": str(uuid.uuid4()),
                "amount": "99.99"
            }
        )
        assert response.status_code == 403
    
    async def test_payment_success_invalid_amount(self, client, valid_api_key):
        """Test payment success with invalid amount"""
        response = client.post(
            "/success",
            json={
                "order_id": str(uuid.uuid4()),
                "amount": "-10"
            },
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 422
    
    async def test_payment_success_invalid_order_id(self, client, valid_api_key):
        """Test payment success with invalid order ID"""
        response = client.post(
            "/success",
            json={
                "order_id": "invalid-uuid",
                "amount": "99.99"
            },
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestPaymentFailed:
    """Test payment failed endpoint"""
    
    async def test_payment_failed_new(self, client, valid_api_key):
        """Test failed payment creation"""
        order_id = uuid.uuid4()
        response = client.post(
            "/failed",
            json={
                "order_id": str(order_id),
                "amount": "99.99"
            },
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["order_id"] == str(order_id)
    
    async def test_payment_failed_update_existing(self, client, valid_api_key, test_payment):
        """Test updating existing payment to failed"""
        response = client.post(
            "/failed",
            json={
                "order_id": str(test_payment.order_id),
                "amount": "149.99"
            },
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
    
    async def test_payment_failed_invalid_api_key(self, client):
        """Test payment failed with invalid API key"""
        response = client.post(
            "/failed",
            json={
                "order_id": str(uuid.uuid4()),
                "amount": "99.99"
            },
            headers={"X-Service-API-Key": "invalid-key"}
        )
        assert response.status_code == 403
    
    async def test_payment_failed_missing_api_key(self, client):
        """Test payment failed without API key"""
        response = client.post(
            "/failed",
            json={
                "order_id": str(uuid.uuid4()),
                "amount": "99.99"
            }
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestGetOrderPayments:
    """Test get order payments endpoint"""
    
    async def test_get_order_payments_success(self, client, valid_api_key, test_payment):
        """Test getting payments for an order"""
        response = client.get(
            f"/orders/{test_payment.order_id}/payments",
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["order_id"] == str(test_payment.order_id)
    
    async def test_get_order_payments_empty(self, client, valid_api_key):
        """Test getting payments for order with no payments"""
        order_id = uuid.uuid4()
        response = client.get(
            f"/orders/{order_id}/payments",
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    async def test_get_order_payments_invalid_api_key(self, client, test_payment):
        """Test getting payments with invalid API key"""
        response = client.get(
            f"/orders/{test_payment.order_id}/payments",
            headers={"X-Service-API-Key": "invalid-key"}
        )
        assert response.status_code == 403
    
    async def test_get_order_payments_missing_api_key(self, client, test_payment):
        """Test getting payments without API key"""
        response = client.get(
            f"/orders/{test_payment.order_id}/payments"
        )
        assert response.status_code == 403
    
    async def test_get_order_payments_invalid_order_id(self, client, valid_api_key):
        """Test getting payments with invalid order ID"""
        response = client.get(
            "/orders/invalid-uuid/payments",
            headers={"X-Service-API-Key": valid_api_key}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test root endpoint"""
    
    async def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"service": "payment-service"}

