from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.CUSTOMER


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
