from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import TicketEventType, TicketStatus
from app.models.ticket_event import TicketEvent


class TicketEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        ticket_id: UUID,
        event_type: TicketEventType,
        actor_id: UUID | None = None,
        from_status: TicketStatus | None = None,
        to_status: TicketStatus | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TicketEvent:
        event = TicketEvent(
            ticket_id=ticket_id,
            event_type=event_type,
            actor_id=actor_id,
            from_status=from_status,
            to_status=to_status,
            event_metadata=metadata,
        )
        self.session.add(event)
        await self.session.flush()
        return event
