from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import (
    ALLOWED_STATUS_TRANSITIONS,
    TicketEventType,
    TicketStatus,
)
from app.exceptions import InvalidStatusTransitionError, NotFoundError
from app.logging import get_logger
from app.models.ticket import Ticket
from app.queue.publisher import TicketProcessingPublisher
from app.repositories.processing_result import ProcessingResultRepository
from app.repositories.ticket import TicketRepository
from app.repositories.ticket_event import TicketEventRepository
from app.repositories.user import UserRepository
from app.schemas.common import Page
from app.schemas.ticket import TicketCreate, TicketDetailResponse

log = get_logger(__name__)


class TicketService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        publisher: TicketProcessingPublisher,
    ) -> None:
        self.session = session
        self.tickets = TicketRepository(session)
        self.users = UserRepository(session)
        self.events = TicketEventRepository(session)
        self.processing = ProcessingResultRepository(session)
        self.publisher = publisher

    async def create_ticket(self, payload: TicketCreate) -> Ticket:
        customer = await self.users.get_or_create_customer(
            email=payload.customer_email,
            name=payload.customer_name,
        )
        ticket = Ticket(
            subject=payload.subject,
            description=payload.description,
            priority=payload.priority,
            category=payload.category,
            status=TicketStatus.OPEN,
            customer_id=customer.id,
        )
        await self.tickets.create(ticket)
        await self.events.record(
            ticket_id=ticket.id,
            event_type=TicketEventType.CREATED,
            actor_id=customer.id,
            to_status=TicketStatus.OPEN,
        )
        await self.processing.upsert_pending(ticket.id)
        await self.session.commit()

        try:
            await self.publisher.publish_created(ticket.id)
        except Exception:
            log.exception("sqs_publish_failed", ticket_id=str(ticket.id))

        return ticket

    async def get_ticket(self, ticket_id: UUID) -> Ticket:
        ticket = await self.tickets.get_with_processing(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        return ticket

    async def list_tickets(self, **filters) -> Page[TicketDetailResponse]:
        offset = filters.pop("offset", 0)
        limit = filters.pop("limit", 20)
        page = filters.pop("page", 1)
        page_size = filters.pop("page_size", limit)

        items, total = await self.tickets.list(offset=offset, limit=limit, **filters)
        return Page[TicketDetailResponse](
            items=[TicketDetailResponse.model_validate(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def _ensure_actor(self, actor_id: UUID | None) -> None:
        if actor_id is None:
            return
        if await self.users.get(actor_id) is None:
            raise NotFoundError(f"Actor {actor_id} not found")

    async def update_status(
        self,
        ticket_id: UUID,
        new_status: TicketStatus,
        actor_id: UUID | None = None,
    ) -> Ticket:
        await self._ensure_actor(actor_id)

        ticket = await self.tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")

        if new_status == ticket.status:
            return ticket

        allowed = ALLOWED_STATUS_TRANSITIONS.get(ticket.status, frozenset())
        if new_status not in allowed:
            raise InvalidStatusTransitionError(
                f"Cannot transition ticket from {ticket.status} to {new_status}",
                details={
                    "from": ticket.status.value,
                    "to": new_status.value,
                    "allowed": sorted(s.value for s in allowed),
                },
            )

        from_status = ticket.status
        ticket.status = new_status
        await self.events.record(
            ticket_id=ticket.id,
            event_type=TicketEventType.STATUS_CHANGED,
            actor_id=actor_id,
            from_status=from_status,
            to_status=new_status,
        )
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def assign_agent(
        self,
        ticket_id: UUID,
        agent_id: UUID | None,
        actor_id: UUID | None = None,
    ) -> Ticket:
        await self._ensure_actor(actor_id)

        ticket = await self.tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")

        if agent_id is not None:
            agent = await self.users.get(agent_id)
            if agent is None:
                raise NotFoundError(f"Agent {agent_id} not found")

        previous = ticket.agent_id
        ticket.agent_id = agent_id

        event_type = (
            TicketEventType.UNASSIGNED if agent_id is None else TicketEventType.ASSIGNED
        )
        await self.events.record(
            ticket_id=ticket.id,
            event_type=event_type,
            actor_id=actor_id,
            metadata={
                "previous_agent_id": str(previous) if previous else None,
                "new_agent_id": str(agent_id) if agent_id else None,
            },
        )
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket
