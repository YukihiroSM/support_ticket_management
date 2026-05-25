from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, *, email: str, name: str, role: UserRole) -> User:
        user = User(email=email, name=name, role=role, is_active=True)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_or_create_customer(self, *, email: str, name: str) -> User:
        existing = await self.get_by_email(email)
        if existing:
            return existing
        return await self.create(email=email, name=name, role=UserRole.CUSTOMER)

    async def list_by_role(
        self,
        role: UserRole,
        *,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        filters = [User.role == role]
        if is_active is not None:
            filters.append(User.is_active == is_active)

        base = select(User).where(*filters)
        total = (
            await self.session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self.session.execute(
                base.order_by(User.created_at.desc()).offset(offset).limit(limit)
            )
        ).scalars().all()
        return list(rows), total

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
