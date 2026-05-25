from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AgentCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
