from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "CUSTOMER"
    AGENT = "AGENT"
    ADMIN = "ADMIN"


class TicketStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TicketCategory(StrEnum):
    TECHNICAL = "TECHNICAL"
    BILLING = "BILLING"
    ACCOUNT = "ACCOUNT"
    GENERAL = "GENERAL"
    OTHER = "OTHER"


class TicketEventType(StrEnum):
    CREATED = "CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    ASSIGNED = "ASSIGNED"
    UNASSIGNED = "UNASSIGNED"
    PRIORITY_CHANGED = "PRIORITY_CHANGED"
    PROCESSED = "PROCESSED"
    COMMENT_ADDED = "COMMENT_ADDED"


class ProcessingStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


ALLOWED_STATUS_TRANSITIONS: dict[TicketStatus, frozenset[TicketStatus]] = {
    TicketStatus.OPEN: frozenset({TicketStatus.IN_PROGRESS, TicketStatus.CLOSED}),
    TicketStatus.IN_PROGRESS: frozenset(
        {TicketStatus.RESOLVED, TicketStatus.OPEN, TicketStatus.CLOSED}
    ),
    TicketStatus.RESOLVED: frozenset({TicketStatus.CLOSED, TicketStatus.IN_PROGRESS}),
    TicketStatus.CLOSED: frozenset(),
}
