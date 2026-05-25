from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_session
from app.queue.publisher import TicketProcessingPublisher
from app.services.ticket_service import TicketService

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_publisher(settings: SettingsDep) -> TicketProcessingPublisher:
    return TicketProcessingPublisher(settings)


PublisherDep = Annotated[TicketProcessingPublisher, Depends(get_publisher)]


async def get_ticket_service(
    session: SessionDep,
    publisher: PublisherDep,
) -> AsyncIterator[TicketService]:
    yield TicketService(session, publisher=publisher)


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
