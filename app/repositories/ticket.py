from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import TicketCategory, TicketPriority, TicketStatus
from app.models.ticket import Ticket


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, ticket_id: UUID) -> Ticket | None:
        return await self.session.get(Ticket, ticket_id)

    async def get_with_processing(self, ticket_id: UUID) -> Ticket | None:
        result = await self.session.execute(
            select(Ticket)
            .options(selectinload(Ticket.processing_result))
            .where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def create(self, ticket: Ticket) -> Ticket:
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def list(
        self,
        *,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        category: TicketCategory | None = None,
        customer_id: UUID | None = None,
        agent_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Ticket], int]:
        filters = []
        if status is not None:
            filters.append(Ticket.status == status)
        if priority is not None:
            filters.append(Ticket.priority == priority)
        if category is not None:
            filters.append(Ticket.category == category)
        if customer_id is not None:
            filters.append(Ticket.customer_id == customer_id)
        if agent_id is not None:
            filters.append(Ticket.agent_id == agent_id)

        base = select(Ticket).where(*filters)

        count_result = await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        page_result = await self.session.execute(
            base.options(selectinload(Ticket.processing_result))
            .order_by(Ticket.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(page_result.scalars().all()), total
