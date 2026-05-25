from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ProcessingStatus, TicketPriority
from app.models.processing_result import TicketProcessingResult


class ProcessingResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_ticket(self, ticket_id: UUID) -> TicketProcessingResult | None:
        result = await self.session.execute(
            select(TicketProcessingResult).where(
                TicketProcessingResult.ticket_id == ticket_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert_pending(self, ticket_id: UUID) -> TicketProcessingResult:
        existing = await self.get_by_ticket(ticket_id)
        if existing:
            existing.processing_status = ProcessingStatus.PENDING
            existing.error_message = None
            return existing
        row = TicketProcessingResult(
            ticket_id=ticket_id,
            processing_status=ProcessingStatus.PENDING,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def save_completed(
        self,
        *,
        ticket_id: UUID,
        auto_summary: str | None,
        suggested_priority: TicketPriority | None,
        spam_score: float | None,
        is_spam: bool | None,
        suggested_department: str | None,
    ) -> TicketProcessingResult:
        row = await self.get_by_ticket(ticket_id) or TicketProcessingResult(
            ticket_id=ticket_id
        )
        row.auto_summary = auto_summary
        row.suggested_priority = suggested_priority
        row.spam_score = spam_score
        row.is_spam = is_spam
        row.suggested_department = suggested_department
        row.processing_status = ProcessingStatus.COMPLETED
        row.error_message = None
        self.session.add(row)
        await self.session.flush()
        return row

    async def save_failed(
        self, *, ticket_id: UUID, error_message: str
    ) -> TicketProcessingResult:
        row = await self.get_by_ticket(ticket_id) or TicketProcessingResult(
            ticket_id=ticket_id
        )
        row.processing_status = ProcessingStatus.FAILED
        row.error_message = error_message
        self.session.add(row)
        await self.session.flush()
        return row
