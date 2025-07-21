from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_logs.model import AuditLog
from src.audit_logs.repository import AuditLogRepository
from src.audit_logs.service import AuditLogService
from src.feature_flags.model import FeatureFlag
from src.feature_flags.repository import FeatureFlagRepository
from src.feature_flags.service import FeatureFlagService
from src.infrastructure.database import Database
from src.common.settings import Settings


class AppContainer(containers.DeclarativeContainer):
    """
    The central dependency injection container for the application.
    """

    settings: providers.Singleton[Settings] = providers.Singleton(Settings)
    db_url_provider: providers.Provider[str] = providers.Factory(
        lambda s: str(s.postgres_dsn),
        s=settings,
    )
    database: providers.Singleton[Database] = providers.Singleton(
        Database,
        db_url=db_url_provider,
    )
    db_session: providers.Factory[AsyncSession] = providers.Factory(
        lambda db: db.get_session(),
        db=database,
    )

    audit_log_repo = providers.Factory(
        AuditLogRepository,
        model=AuditLog,
        db_session=db_session,
    )
    feature_flag_repo = providers.Factory(
        FeatureFlagRepository,
        model=FeatureFlag,
        db_session=db_session,
    )

    audit_log_service = providers.Factory(AuditLogService, repository=audit_log_repo)
    feature_flag_service = providers.Factory(
        FeatureFlagService, repository=feature_flag_repo
    )
