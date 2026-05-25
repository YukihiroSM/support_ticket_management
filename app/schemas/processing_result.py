from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.enums import ProcessingStatus, TicketPriority


class ProcessingResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    auto_summary: str | None
    suggested_priority: TicketPriority | None
    spam_score: float | None
    is_spam: bool | None
    suggested_department: str | None
    processed_at: datetime
    processing_status: ProcessingStatus
    error_message: str | None
