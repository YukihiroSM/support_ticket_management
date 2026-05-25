from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import TicketServiceDep
from app.enums import TicketCategory, TicketPriority, TicketStatus
from app.schemas.common import Page
from app.schemas.ticket import (
    TicketAssign,
    TicketCreate,
    TicketDetailResponse,
    TicketResponse,
    TicketStatusUpdate,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a support ticket",
)
async def create_ticket(
    payload: TicketCreate,
    service: TicketServiceDep,
) -> TicketResponse:
    ticket = await service.create_ticket(payload)
    return TicketResponse.model_validate(ticket)


@router.get(
    "",
    response_model=Page[TicketDetailResponse],
    summary="List tickets with filters and pagination",
)
async def list_tickets(
    service: TicketServiceDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: TicketStatus | None = Query(None, alias="status"),
    priority: TicketPriority | None = Query(None),
    category: TicketCategory | None = Query(None),
    customer_id: UUID | None = Query(None),
    agent_id: UUID | None = Query(None),
) -> Page[TicketDetailResponse]:
    offset = (page - 1) * page_size
    return await service.list_tickets(
        status=status_filter,
        priority=priority,
        category=category,
        customer_id=customer_id,
        agent_id=agent_id,
        offset=offset,
        limit=page_size,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Retrieve a ticket by ID",
)
async def get_ticket(
    ticket_id: UUID,
    service: TicketServiceDep,
) -> TicketDetailResponse:
    ticket = await service.get_ticket(ticket_id)
    return TicketDetailResponse.model_validate(ticket)


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
    summary="Update ticket status (validates allowed transitions)",
)
async def update_status(
    ticket_id: UUID,
    payload: TicketStatusUpdate,
    service: TicketServiceDep,
) -> TicketResponse:
    ticket = await service.update_status(ticket_id, payload.status, payload.actor_id)
    return TicketResponse.model_validate(ticket)


@router.patch(
    "/{ticket_id}/assignment",
    response_model=TicketResponse,
    summary="Assign or unassign an agent",
)
async def assign_agent(
    ticket_id: UUID,
    payload: TicketAssign,
    service: TicketServiceDep,
) -> TicketResponse:
    ticket = await service.assign_agent(ticket_id, payload.agent_id, payload.actor_id)
    return TicketResponse.model_validate(ticket)
