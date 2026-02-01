from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select
from database import engine, Base, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from schemas import UserRegisterRequest, UserResponse, UserLoginRequest, LoginResponse
from auth import hash_password, verify_password, create_access_token

app = FastAPI(
    title="User Service",
    description="User management service with registration and authentication endpoints",
    version="1.0.0"
)


@app.on_event("startup")
async def startup():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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

