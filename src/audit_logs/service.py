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
        *,
        log_data: AuditLogCreate,
    ) -> None:
        """
        Creates and saves a new audit log entry from a Pydantic schema.

        :param log_data: A Pydantic schema containing all necessary audit data.
        """
        await self.repository.create(obj_in=log_data)

    async def get_history(
        self,
        *,
        query: AuditLogHistoryQuery,
    ) -> list[AuditLog]:
        """
        Fetches a paginated history of audit logs based on query parameters.

        :param query: A Pydantic object containing all filter and pagination options.
        :return: A list of audit log model instances.
        """
        return await self.repository.get_history(query)
