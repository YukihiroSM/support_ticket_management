import json
from typing import Any
from uuid import UUID

from app.config import Settings
from app.logging import get_logger
from app.queue.sqs import sqs_client

log = get_logger(__name__)


class TicketProcessingPublisher:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def publish_created(self, ticket_id: UUID) -> None:
        body: dict[str, Any] = {
            "event": "ticket.created",
            "ticket_id": str(ticket_id),
        }
        async with sqs_client(self.settings) as client:
            await client.send_message(
                QueueUrl=self.settings.sqs_queue_url,
                MessageBody=json.dumps(body),
            )
        log.info(
            "ticket_event_published",
            event_name="ticket.created",
            ticket_id=str(ticket_id),
        )
