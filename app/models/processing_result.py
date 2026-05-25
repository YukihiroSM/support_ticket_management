from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import ProcessingStatus, TicketPriority
from app.models.base import Base, UUIDPrimaryKeyMixin


class TicketProcessingResult(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ticket_processing_results"
    __table_args__ = (
        Index("ix_ticket_processing_results_status", "processing_status"),
    )

    ticket_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    auto_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_priority: Mapped[TicketPriority | None] = mapped_column(
        Enum(
            TicketPriority, name="ticket_priority", native_enum=True, create_type=False
        ),
        nullable=True,
    )
    spam_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_spam: Mapped[bool | None] = mapped_column(nullable=True)
    suggested_department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status", native_enum=True),
        nullable=False,
        default=ProcessingStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    ticket = relationship("Ticket", back_populates="processing_result")
