from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import TicketCategory, TicketPriority, TicketStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Ticket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_priority", "priority"),
        Index("ix_tickets_category", "category"),
        Index("ix_tickets_customer_id", "customer_id"),
        Index("ix_tickets_agent_id", "agent_id"),
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_created_at", "created_at"),
    )

    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority", native_enum=True),
        nullable=False,
        default=TicketPriority.MEDIUM,
    )
    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory, name="ticket_category", native_enum=True),
        nullable=False,
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", native_enum=True),
        nullable=False,
        default=TicketStatus.OPEN,
    )

    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    agent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    customer = relationship(
        "User", back_populates="tickets_as_customer", foreign_keys=[customer_id]
    )
    agent = relationship(
        "User", back_populates="tickets_as_agent", foreign_keys=[agent_id]
    )
    events = relationship(
        "TicketEvent",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketEvent.created_at",
    )
    processing_result = relationship(
        "TicketProcessingResult",
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan",
    )
