from pydantic import BaseModel
from sqlalchemy import select

from src.infrastructure.base_repository import BaseRepository
from .model import AuditLog
from .schemas import AuditLogCreate, AuditLogHistoryQuery
from typing import Any, Generic, Type, TypeVar
from src.infrastructure.database import Base


ModelType = TypeVar("ModelType", bound=Base)


class AuditLogRepository(BaseRepository[AuditLog, AuditLogCreate, BaseModel]):
    async def get_history(
        self,
        *,
        query: AuditLogHistoryQuery,
    ) -> list[AuditLog]:
        """
        Fetches a paginated history of audit logs.

        :param query: A Pydantic object containing all filter and pagination options.
        :return: A list of audit log model instances.
        """
        statement = select(self.model).order_by(self.model.timestamp.desc())

        if query.target_entity:
            statement = statement.where(self.model.target_entity == query.target_entity)

        if query.target_id:
            statement = statement.where(self.model.target_id == query.target_id)

        if query.action:
            statement = statement.where(self.model.action == query.action)

        # Apply pagination from the query object
        statement = statement.offset(query.skip).limit(query.limit)

        result = await self.db.execute(statement)
        return result.scalars().all()
