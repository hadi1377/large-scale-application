from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from database import engine, Base, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from schemas import UserRegisterRequest, UserResponse, UserLoginRequest, LoginResponse
from auth import hash_password, verify_password, create_access_token, verify_token

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown (no cleanup needed)


app = FastAPI(
    title="User Service",
    description="User management service with registration and authentication endpoints",
    version="1.0.0",
    lifespan=lifespan
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
            "description": "Enter your JWT token (from /login endpoint)"
        }
    }
    
    # Add security requirement to /me endpoint
    if "paths" in openapi_schema and "/me" in openapi_schema["paths"]:
        openapi_schema["paths"]["/me"]["get"]["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/")
def root():
    return {"service": "user-service"}


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    
    - **email**: User's email address (must be unique)
    - **password**: User's password (will be hashed)
    - **full_name**: User's full name
    
    All registered users will have main_role set to "user".
    """
    # Check if user with this email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user (main_role is always "user" for registrations)
    new_user = User(
        email=user_data.email,
        password=hash_password(user_data.password),
        full_name=user_data.full_name,
        main_role="user"
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(login_data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login a user.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns user information if credentials are valid.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.main_role})
    
    # Return user information with token
    return LoginResponse(
        access_token=access_token,
        user=user
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from the JWT token."""
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@app.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(oauth2_scheme)]
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    
    Requires a valid JWT token in the Authorization header.
    
    **How to use:**
    1. Login using `/login` endpoint to get your access token
    2. Click the "Authorize" button at the top of this page
    3. Enter your token (just the token, without "Bearer" prefix)
    4. Click "Authorize" and then "Close"
    5. Now you can use the "Try it out" button on this endpoint
    """
    return current_user


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def get_user_by_id(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get user information by ID.
    
    This is an internal endpoint for service-to-service communication.
    Used by other services (e.g., notification-service) to fetch user details.
    """
    import uuid as uuid_lib
    
    # Validate user_id format
    try:
        user_uuid = uuid_lib.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user
