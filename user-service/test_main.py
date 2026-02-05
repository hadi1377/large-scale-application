import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import String, Column, DateTime
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
import tempfile
import os
import atexit
from datetime import datetime, timezone

from main import app
from database import get_db
from models import User
from auth import hash_password, verify_password, create_access_token, verify_token


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

# Import Base and modify for SQLite
from database import Base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Create a custom type that converts UUID to String for SQLite
from sqlalchemy import TypeDecorator

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


@pytest.fixture(scope="function")
def client():
    """Create test client"""
    return TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def test_user():
    """Create a test user for authentication tests"""
    # Ensure tables exist before creating user
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    user_id = str(uuid.uuid4())
    # Use a unique email for each test to avoid conflicts
    unique_email = f"test_{user_id}@example.com"
    
    async with TestingSessionLocal() as session:
        # Check if user already exists and delete it
        from sqlalchemy import select
        try:
            result = await session.execute(
                select(User).where(User.email == unique_email)
            )
            existing = result.scalar_one_or_none()
            if existing:
                await session.delete(existing)
                await session.commit()
        except Exception:
            # If table doesn't exist, create it
            await session.rollback()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        
        # Create user with string ID for SQLite compatibility
        user = User(
            id=user_id,
            email=unique_email,
            password=hash_password("testpassword123"),
            full_name="Test User",
            main_role="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Create a simple object to hold user data for tests
        class TestUserData:
            def __init__(self, user_obj, email):
                self.id = user_id
                self.email = email
                self.main_role = user_obj.main_role
                self.full_name = user_obj.full_name
        return TestUserData(user, unique_email)


class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["main_role"] == "user"
        assert "id" in data
        assert "password" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        # Try to register with the same email as test_user
        response = client.post(
            "/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post(
            "/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post(
            "/register",
            json={
                "email": "test@example.com"
            }
        )
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email
        assert "password" not in data["user"]
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post(
            "/login",
            json={
                "email": "test@example.com"
            }
        )
        assert response.status_code == 422


class TestGetMe:
    """Test /me endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_me_success(self, client, test_user):
        """Test getting current user info with valid token"""
        # Create token
        token = create_access_token(data={"sub": str(test_user.id), "email": test_user.email, "role": test_user.main_role})
        
        response = client.get(
            "/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)
    
    def test_get_me_invalid_token(self, client):
        """Test /me with invalid token"""
        response = client.get(
            "/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_get_me_missing_token(self, client):
        """Test /me without token"""
        response = client.get("/me")
        assert response.status_code == 401
    
    def test_get_me_expired_token(self, client):
        """Test /me with expired token"""
        from datetime import timedelta
        expired_token = create_access_token(
            data={"sub": str(uuid.uuid4()), "email": "test@example.com", "role": "user"},
            expires_delta=timedelta(seconds=-1)  # Expired token
        )
        response = client.get(
            "/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401


class TestGetUserById:
    """Test /users/{user_id} endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, client, test_user):
        """Test getting user by ID"""
        response = client.get(f"/users/{test_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
    
    def test_get_user_by_id_not_found(self, client):
        """Test getting non-existent user"""
        fake_id = uuid.uuid4()
        response = client.get(f"/users/{fake_id}")
        assert response.status_code == 404
    
    def test_get_user_by_id_invalid_format(self, client):
        """Test getting user with invalid ID format"""
        response = client.get("/users/invalid-id")
        assert response.status_code == 400


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"service": "user-service"}


class TestAuthFunctions:
    """Test authentication utility functions"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password(self):
        """Test password verification"""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_create_access_token(self):
        """Test token creation"""
        data = {"sub": str(uuid.uuid4()), "email": "test@example.com", "role": "user"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token(self):
        """Test token verification"""
        data = {"sub": str(uuid.uuid4()), "email": "test@example.com", "role": "user"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        with pytest.raises(ValueError):
            verify_token("invalid_token")

