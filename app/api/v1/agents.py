from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import SessionDep
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from app.schemas.common import Page
from app.services.agent_service import AgentService


async def get_agent_service(session: SessionDep) -> AgentService:
    return AgentService(session)


AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an agent",
)
async def create_agent(
    payload: AgentCreate,
    service: AgentServiceDep,
) -> AgentResponse:
    agent = await service.create(payload)
    return AgentResponse.model_validate(agent)


@router.get(
    "",
    response_model=Page[AgentResponse],
    summary="List agents",
)
async def list_agents(
    service: AgentServiceDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
) -> Page[AgentResponse]:
    return await service.list(is_active=is_active, page=page, page_size=page_size)


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get an agent by ID",
)
async def get_agent(
    agent_id: UUID,
    service: AgentServiceDep,
) -> AgentResponse:
    agent = await service.get(agent_id)
    return AgentResponse.model_validate(agent)


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update an agent (name, active flag)",
)
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    service: AgentServiceDep,
) -> AgentResponse:
    agent = await service.update(agent_id, payload)
    return AgentResponse.model_validate(agent)


@router.delete(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Deactivate an agent (soft delete)",
)
async def deactivate_agent(
    agent_id: UUID,
    service: AgentServiceDep,
) -> AgentResponse:
    agent = await service.deactivate(agent_id)
    return AgentResponse.model_validate(agent)
