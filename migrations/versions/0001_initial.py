"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


USER_ROLE = postgresql.ENUM("CUSTOMER", "AGENT", "ADMIN", name="user_role")
TICKET_STATUS = postgresql.ENUM(
    "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED", name="ticket_status"
)
TICKET_PRIORITY = postgresql.ENUM(
    "LOW", "MEDIUM", "HIGH", "URGENT", name="ticket_priority"
)
TICKET_CATEGORY = postgresql.ENUM(
    "TECHNICAL", "BILLING", "ACCOUNT", "GENERAL", "OTHER", name="ticket_category"
)
TICKET_EVENT_TYPE = postgresql.ENUM(
    "CREATED",
    "STATUS_CHANGED",
    "ASSIGNED",
    "UNASSIGNED",
    "PRIORITY_CHANGED",
    "PROCESSED",
    "COMMENT_ADDED",
    name="ticket_event_type",
)
PROCESSING_STATUS = postgresql.ENUM(
    "PENDING", "COMPLETED", "FAILED", name="processing_status"
)


def upgrade() -> None:
    bind = op.get_bind()
    USER_ROLE.create(bind, checkfirst=True)
    TICKET_STATUS.create(bind, checkfirst=True)
    TICKET_PRIORITY.create(bind, checkfirst=True)
    TICKET_CATEGORY.create(bind, checkfirst=True)
    TICKET_EVENT_TYPE.create(bind, checkfirst=True)
    PROCESSING_STATUS.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "tickets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            postgresql.ENUM(name="ticket_priority", create_type=False),
            nullable=False,
            server_default="MEDIUM",
        ),
        sa.Column(
            "category",
            postgresql.ENUM(name="ticket_category", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="ticket_status", create_type=False),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_priority", "tickets", ["priority"])
    op.create_index("ix_tickets_category", "tickets", ["category"])
    op.create_index("ix_tickets_customer_id", "tickets", ["customer_id"])
    op.create_index("ix_tickets_agent_id", "tickets", ["agent_id"])
    op.create_index("ix_tickets_status_priority", "tickets", ["status", "priority"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])

    op.create_table(
        "ticket_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            postgresql.ENUM(name="ticket_event_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "from_status",
            postgresql.ENUM(name="ticket_status", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "to_status",
            postgresql.ENUM(name="ticket_status", create_type=False),
            nullable=True,
        ),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_ticket_events_ticket_id", "ticket_events", ["ticket_id"])
    op.create_index(
        "ix_ticket_events_ticket_created", "ticket_events", ["ticket_id", "created_at"]
    )
    op.create_index("ix_ticket_events_event_type", "ticket_events", ["event_type"])

    op.create_table(
        "ticket_processing_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("auto_summary", sa.Text(), nullable=True),
        sa.Column(
            "suggested_priority",
            postgresql.ENUM(name="ticket_priority", create_type=False),
            nullable=True,
        ),
        sa.Column("spam_score", sa.Float(), nullable=True),
        sa.Column("is_spam", sa.Boolean(), nullable=True),
        sa.Column("suggested_department", sa.String(length=255), nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "processing_status",
            postgresql.ENUM(name="processing_status", create_type=False),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_ticket_processing_results_status",
        "ticket_processing_results",
        ["processing_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_ticket_processing_results_status", "ticket_processing_results")
    op.drop_table("ticket_processing_results")

    op.drop_index("ix_ticket_events_event_type", "ticket_events")
    op.drop_index("ix_ticket_events_ticket_created", "ticket_events")
    op.drop_index("ix_ticket_events_ticket_id", "ticket_events")
    op.drop_table("ticket_events")

    op.drop_index("ix_tickets_created_at", "tickets")
    op.drop_index("ix_tickets_status_priority", "tickets")
    op.drop_index("ix_tickets_agent_id", "tickets")
    op.drop_index("ix_tickets_customer_id", "tickets")
    op.drop_index("ix_tickets_category", "tickets")
    op.drop_index("ix_tickets_priority", "tickets")
    op.drop_index("ix_tickets_status", "tickets")
    op.drop_table("tickets")

    op.drop_index("ix_users_role", "users")
    op.drop_table("users")

    bind = op.get_bind()
    PROCESSING_STATUS.drop(bind, checkfirst=True)
    TICKET_EVENT_TYPE.drop(bind, checkfirst=True)
    TICKET_CATEGORY.drop(bind, checkfirst=True)
    TICKET_PRIORITY.drop(bind, checkfirst=True)
    TICKET_STATUS.drop(bind, checkfirst=True)
    USER_ROLE.drop(bind, checkfirst=True)
