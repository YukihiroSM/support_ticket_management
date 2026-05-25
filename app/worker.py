"""SQS consumer that processes ticket-created events.

Run with: `python -m app.worker`
"""

from __future__ import annotations

import asyncio
import json
import signal
from typing import Any
from uuid import UUID

from botocore.exceptions import ClientError

from app.config import get_settings
from app.database import SessionLocal
from app.logging import configure_logging, get_logger
from app.queue.sqs import sqs_client
from app.services.processing_service import TicketProcessingService

log = get_logger(__name__)

# SQS returns this code when the queue isn't there yet (e.g. LocalStack init
# is still running). Retry quietly instead of dumping a stacktrace.
_QUEUE_MISSING_CODES = frozenset(
    {"AWS.SimpleQueueService.NonExistentQueue", "QueueDoesNotExist"}
)
_QUEUE_MISSING_BACKOFF_SECONDS = 3


class Worker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._stop = asyncio.Event()

    def request_stop(self) -> None:
        log.info("worker_stop_requested")
        self._stop.set()

    async def run(self) -> None:
        log.info(
            "worker_starting",
            queue=self.settings.sqs_queue_url,
            endpoint=self.settings.aws_endpoint_url,
        )
        async with sqs_client(self.settings) as client:
            while not self._stop.is_set():
                try:
                    response = await client.receive_message(
                        QueueUrl=self.settings.sqs_queue_url,
                        MaxNumberOfMessages=self.settings.worker_max_messages,
                        WaitTimeSeconds=self.settings.worker_poll_wait_seconds,
                    )
                except ClientError as exc:
                    code = exc.response.get("Error", {}).get("Code", "")
                    if code in _QUEUE_MISSING_CODES:
                        log.warning(
                            "worker_queue_not_ready",
                            queue=self.settings.sqs_queue_url,
                            backoff_seconds=_QUEUE_MISSING_BACKOFF_SECONDS,
                        )
                        await asyncio.sleep(_QUEUE_MISSING_BACKOFF_SECONDS)
                        continue
                    log.exception("worker_receive_failed")
                    await asyncio.sleep(2)
                    continue
                except Exception:
                    log.exception("worker_receive_failed")
                    await asyncio.sleep(2)
                    continue

                messages = response.get("Messages", [])
                if not messages:
                    continue

                for message in messages:
                    await self._handle_message(client, message)

        log.info("worker_stopped")

    async def _handle_message(self, client, message: dict[str, Any]) -> None:
        receipt = message["ReceiptHandle"]
        body_raw = message.get("Body", "")

        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            log.error("worker_invalid_json", body=body_raw)
            await client.delete_message(
                QueueUrl=self.settings.sqs_queue_url, ReceiptHandle=receipt
            )
            return

        event = body.get("event")
        ticket_id_raw = body.get("ticket_id")

        if event != "ticket.created" or not ticket_id_raw:
            log.warning("worker_unknown_event", body=body)
            await client.delete_message(
                QueueUrl=self.settings.sqs_queue_url, ReceiptHandle=receipt
            )
            return

        ticket_id = UUID(ticket_id_raw)

        try:
            async with SessionLocal() as session:
                service = TicketProcessingService(session)
                await service.process(ticket_id)
        except Exception as exc:
            log.exception("worker_processing_failed", ticket_id=str(ticket_id))
            try:
                async with SessionLocal() as session:
                    await TicketProcessingService(session).record_failure(
                        ticket_id, str(exc)
                    )
            except Exception:
                log.exception("worker_failure_record_failed", ticket_id=str(ticket_id))
            # Leave message in flight; SQS will retry per RedrivePolicy.
            return

        await client.delete_message(
            QueueUrl=self.settings.sqs_queue_url, ReceiptHandle=receipt
        )
        log.info("worker_ticket_processed", ticket_id=str(ticket_id))


def _install_signal_handlers(worker: Worker, loop: asyncio.AbstractEventLoop) -> None:
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, worker.request_stop)


def main() -> None:
    configure_logging()
    worker = Worker()
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        _install_signal_handlers(worker, loop)
        loop.run_until_complete(worker.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
