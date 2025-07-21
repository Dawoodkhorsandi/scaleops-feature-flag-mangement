import asyncio
import logging

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_scoped_session,
)
from sqlalchemy.orm import sessionmaker, declarative_base


# --- Module-level setup ---
logger = logging.getLogger(__name__)
Base = declarative_base()


# --- Class-based Database Management ---
class Database:
    """
    Manages the database connection, engine, and session creation.
    This class encapsulates the session lifecycle management.
    """

    def __init__(self, db_url: str):
        """
        Initializes the async engine and the scoped session factory.
        """
        self._engine = create_async_engine(db_url, echo=False)
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._session_factory = async_scoped_session(
            session_factory,
            scopefunc=asyncio.current_task,
        )

    def get_session(self) -> AsyncSession:
        """Returns the session for the current async context."""
        return self._session_factory()

    async def close_session(self):
        """Closes and removes the session for the current context."""
        await self._session_factory.remove()
