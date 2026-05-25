import hashlib
import random
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import TicketCategory, TicketEventType, TicketPriority
from app.exceptions import NotFoundError
from app.logging import get_logger
from app.repositories.processing_result import ProcessingResultRepository
from app.repositories.ticket import TicketRepository
from app.repositories.ticket_event import TicketEventRepository

log = get_logger(__name__)

CATEGORY_TO_DEPARTMENT: dict[TicketCategory, str] = {
    TicketCategory.TECHNICAL: "engineering",
    TicketCategory.BILLING: "finance",
    TicketCategory.ACCOUNT: "customer-success",
    TicketCategory.GENERAL: "support",
    TicketCategory.OTHER: "triage",
}


class TicketProcessingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tickets = TicketRepository(session)
        self.events = TicketEventRepository(session)
        self.processing = ProcessingResultRepository(session)

    async def process(self, ticket_id: UUID) -> None:
        ticket = await self.tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")

        rng = random.Random(
            int(hashlib.sha256(str(ticket.id).encode()).hexdigest(), 16)
        )

        summary = ticket.description[:200] + (
            "…" if len(ticket.description) > 200 else ""
        )
        spam_score = round(rng.random(), 3)
        is_spam = spam_score > 0.4
        suggested_priority = self._heuristic_priority(
            ticket.subject, ticket.description
        )
        suggested_department = CATEGORY_TO_DEPARTMENT.get(ticket.category, "triage")

        await self.processing.save_completed(
            ticket_id=ticket.id,
            auto_summary=summary,
            suggested_priority=suggested_priority,
            spam_score=spam_score,
            is_spam=is_spam,
            suggested_department=suggested_department,
        )
        await self.events.record(
            ticket_id=ticket.id,
            event_type=TicketEventType.PROCESSED,
            metadata={
                "suggested_priority": suggested_priority.value,
                "suggested_department": suggested_department,
                "is_spam": is_spam,
            },
        )
        await self.session.commit()

    async def record_failure(self, ticket_id: UUID, error: str) -> None:
        await self.processing.save_failed(ticket_id=ticket_id, error_message=error)
        await self.session.commit()

    @staticmethod
    def _heuristic_priority(subject: str, description: str) -> TicketPriority:
        text = f"{subject} {description}".lower()
        if any(kw in text for kw in ("urgent", "critical", "outage", "down", "broken")):
            return TicketPriority.URGENT
        if any(kw in text for kw in ("error", "fail", "bug", "cannot", "can't")):
            return TicketPriority.HIGH
        if any(kw in text for kw in ("question", "how", "help")):
            return TicketPriority.LOW
        return TicketPriority.MEDIUM
