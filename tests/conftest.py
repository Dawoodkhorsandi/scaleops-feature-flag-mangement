import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app import create_app
from src.audit_logs.model import AuditLog
from src.audit_logs.repository import AuditLogRepository
from src.common.settings import Settings
from src.feature_flags.model import FeatureFlag
from src.feature_flags.repository import FeatureFlagRepository
from src.infrastructure.containers import AppContainer
from src.infrastructure.database import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(_env_file=".env.test")


@pytest.fixture(scope="function")
async def setup_database(test_settings: Settings) -> AsyncGenerator[None, None]:
    engine = create_async_engine(str(test_settings.postgres_dsn))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


@pytest.fixture
async def db_session(
    test_settings: Settings,
    setup_database: None,  # Depends on the function-scoped setup
) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(str(test_settings.postgres_dsn))
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session
        await session.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Creates a test client that properly manages the app's lifespan,
    ensuring that dependency injection is wired before tests run.
    """
    app = create_app()
    container: AppContainer = app.container
    container.db_session.override(db_session)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as test_client:
            yield test_client


@pytest.fixture
def feature_flag_repo(db_session: AsyncSession) -> FeatureFlagRepository:
    """Provides a repository instance for feature flags with the test session."""
    return FeatureFlagRepository(model=FeatureFlag, db_session=db_session)


@pytest.fixture
def audit_log_repo(db_session: AsyncSession) -> AuditLogRepository:
    """Provides a repository instance for audit logs with the test session."""
    return AuditLogRepository(model=AuditLog, db_session=db_session)
