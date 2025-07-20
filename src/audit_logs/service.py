from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .model import AuditLog

from .schemas import AuditLogCreate, AuditLogHistoryQuery
from .repository import AuditLogRepository

class AuditLogService:
    """
    The service layer containing business logic for audit logs.
    It depends on the repository for data access.
    """

    def __init__(self, repository: AuditLogRepository):
        """
        Initializes the service with a repository dependency.
        This is ideal for dependency injection.

        :param repository: An instance of AuditLogRepository.
        """
        self.repository = repository

    async def create_log(
        self,
        db: AsyncSession,
        *,
        log_data: AuditLogCreate,
    ) -> None:
        """
        Creates and saves a new audit log entry from a Pydantic schema.
        This method uses the "Parameter Object" pattern for clean, maintainable code.

        :param db: The async database session.
        :param log_data: A Pydantic schema containing all necessary audit data.
        """
        await self.repository.create(db=db, obj_in=log_data)

    async def get_history(
        self,
        db: AsyncSession,
        *,
        query: AuditLogHistoryQuery,
    ) -> list[AuditLog]:
        """
        Fetches a paginated history of audit logs based on query parameters.

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