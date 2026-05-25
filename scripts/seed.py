"""Seed the database with a few users and tickets for quick testing.

Run inside the api container:
    docker compose run --rm api python -m scripts.seed
Or locally with DATABASE_URL set:
    python -m scripts.seed
"""

from __future__ import annotations

import asyncio

from app.database import SessionLocal
from app.enums import TicketCategory, TicketPriority, TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.user import User


async def seed() -> None:
    async with SessionLocal() as session:
        customer = User(
            email="alice@example.com", name="Alice Customer", role=UserRole.CUSTOMER
        )
        agent = User(email="bob@example.com", name="Bob Agent", role=UserRole.AGENT)
        admin = User(email="carol@example.com", name="Carol Admin", role=UserRole.ADMIN)
        session.add_all([customer, agent, admin])
        await session.flush()

        tickets = [
            Ticket(
                subject="Cannot log in",
                description="I get an error when entering my password.",
                priority=TicketPriority.HIGH,
                category=TicketCategory.ACCOUNT,
                status=TicketStatus.OPEN,
                customer_id=customer.id,
            ),
            Ticket(
                subject="Invoice question",
                description="Why was I charged twice this month?",
                priority=TicketPriority.MEDIUM,
                category=TicketCategory.BILLING,
                status=TicketStatus.OPEN,
                customer_id=customer.id,
            ),
            Ticket(
                subject="Feature request: dark mode",
                description="It would be great to have dark mode in settings.",
                priority=TicketPriority.LOW,
                category=TicketCategory.GENERAL,
                status=TicketStatus.IN_PROGRESS,
                customer_id=customer.id,
                agent_id=agent.id,
            ),
        ]
        session.add_all(tickets)

        await session.commit()
        print(f"Seeded {len([customer, agent, admin])} users, {len(tickets)} tickets.")


if __name__ == "__main__":
    asyncio.run(seed())
