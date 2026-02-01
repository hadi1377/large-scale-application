from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    main_role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

