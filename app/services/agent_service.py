from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from app.schemas.common import Page


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def create(self, payload: AgentCreate) -> User:
        if await self.users.get_by_email(payload.email):
            raise ConflictError(
                f"User with email {payload.email} already exists",
                details={"email": payload.email},
            )
        agent = await self.users.create(
            email=payload.email, name=payload.name, role=UserRole.AGENT
        )
        await self.session.commit()
        return agent

    async def get(self, agent_id: UUID) -> User:
        agent = await self.users.get(agent_id)
        if agent is None or agent.role != UserRole.AGENT:
            raise NotFoundError(f"Agent {agent_id} not found")
        return agent

    async def list(
        self,
        *,
        is_active: bool | None,
        page: int,
        page_size: int,
    ) -> Page[AgentResponse]:
        offset = (page - 1) * page_size
        items, total = await self.users.list_by_role(
            UserRole.AGENT,
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )
        return Page[AgentResponse](
            items=[AgentResponse.model_validate(u) for u in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update(self, agent_id: UUID, payload: AgentUpdate) -> User:
        agent = await self.get(agent_id)
        if payload.name is not None:
            agent.name = payload.name
        if payload.is_active is not None:
            agent.is_active = payload.is_active
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def deactivate(self, agent_id: UUID) -> User:
        """Soft-delete: tickets reference agent_id, so we flip is_active off."""
        agent = await self.get(agent_id)
        agent.is_active = False
        await self.session.commit()
        await self.session.refresh(agent)
        return agent
