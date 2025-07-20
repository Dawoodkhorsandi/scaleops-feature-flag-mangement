from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.base_repository import BaseRepository
from .model import AuditLog
from .schema import AuditLogCreate, AuditLogHistoryQuery


class AuditLogRepository(
    BaseRepository[AuditLog, AuditLogCreate, BaseModel]
):
    """
    Repository for AuditLog data access operations.

    Inherits basic CRUD functionality from BaseRepository and adds
    specific querying methods for retrieving audit history.
    """

    async def get_history(
        self,
        db: AsyncSession,
        *,
        query: AuditLogHistoryQuery,
    ) -> list[AuditLog]:
        """
        Fetches a paginated history of audit logs based on query parameters.

        This method encapsulates the database query logic, keeping the service
        layer clean and focused on business rules.

        :param db: The async database session.
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

        result = await db.execute(statement)
        return result.scalars().all()
