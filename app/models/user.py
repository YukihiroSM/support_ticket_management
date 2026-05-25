from sqlalchemy import Boolean, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import UserRole
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_role", "role"),)

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tickets_as_customer = relationship(
        "Ticket",
        back_populates="customer",
        foreign_keys="Ticket.customer_id",
    )
    tickets_as_agent = relationship(
        "Ticket",
        back_populates="agent",
        foreign_keys="Ticket.agent_id",
    )
