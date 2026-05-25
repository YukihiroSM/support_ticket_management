from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import TicketEventType, TicketStatus
from app.models.base import Base, UUIDPrimaryKeyMixin


class TicketEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ticket_events"
    __table_args__ = (
        Index("ix_ticket_events_ticket_id", "ticket_id"),
        Index("ix_ticket_events_ticket_created", "ticket_id", "created_at"),
        Index("ix_ticket_events_event_type", "event_type"),
    )

    ticket_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[TicketEventType] = mapped_column(
        Enum(TicketEventType, name="ticket_event_type", native_enum=True),
        nullable=False,
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_status: Mapped[TicketStatus | None] = mapped_column(
        Enum(TicketStatus, name="ticket_status", native_enum=True, create_type=False),
        nullable=True,
    )
    to_status: Mapped[TicketStatus | None] = mapped_column(
        Enum(TicketStatus, name="ticket_status", native_enum=True, create_type=False),
        nullable=True,
    )
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    ticket = relationship("Ticket", back_populates="events")
