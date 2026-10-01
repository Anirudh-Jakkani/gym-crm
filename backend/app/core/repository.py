import uuid
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base


class TenantRepository[ModelT: Base]:
    """Data access for a tenant-owned model. Every query is filtered by gym_id,
    so a record from another gym behaves exactly like a missing record (404)."""

    model: type[ModelT]

    def __init__(self, db: AsyncSession, gym_id: uuid.UUID):
        self.db = db
        self.gym_id = gym_id

    def query(self) -> Select[tuple[ModelT]]:
        return select(self.model).where(self.model.gym_id == self.gym_id)

    async def get(self, obj_id: uuid.UUID) -> ModelT | None:
        return await self.db.scalar(self.query().where(self.model.id == obj_id))

    async def get_or_404(self, obj_id: uuid.UUID) -> ModelT:
        obj = await self.get(obj_id)
        if obj is None:
            name = self.model.__name__.replace("_", " ")
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} not found")
        return obj

    async def list(self, stmt: Select | None = None) -> Sequence[ModelT]:
        result = await self.db.scalars(stmt if stmt is not None else self.query())
        return result.all()

    async def count(self, stmt: Select | None = None) -> int:
        base = stmt if stmt is not None else self.query()
        return await self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

    async def create(self, **values: Any) -> ModelT:
        obj = self.model(**values, gym_id=self.gym_id)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def update(self, obj: ModelT, values: dict[str, Any]) -> ModelT:
        for key, value in values.items():
            setattr(obj, key, value)
        await self.db.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.db.delete(obj)
        await self.db.flush()
