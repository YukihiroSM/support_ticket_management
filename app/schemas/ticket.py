from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import TicketCategory, TicketPriority, TicketStatus
from app.schemas.processing_result import ProcessingResultResponse


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=255)
    customer_email: EmailStr
    subject: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    priority: TicketPriority = TicketPriority.MEDIUM
    category: TicketCategory


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    actor_id: UUID | None = Field(
        default=None,
    )


class TicketAssign(BaseModel):
    agent_id: UUID | None = Field(
        default=None,
    )
    actor_id: UUID | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject: str
    description: str
    priority: TicketPriority
    category: TicketCategory
    status: TicketStatus
    customer_id: UUID
    agent_id: UUID | None
    created_at: datetime
    updated_at: datetime


class TicketDetailResponse(TicketResponse):
    processing_result: ProcessingResultResponse | None = None
