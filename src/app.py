from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.audit_logs.events import register_audit_listeners
from src.audit_logs.router import router as audit_logs_router
from src.feature_flags.router import router as feature_flags_router

from src.infrastructure.containers import AppContainer
from src.infrastructure.database import Database
from src.middlewares.db_session import DBSessionMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events gracefully.
    """
    app.container.wire(
        modules=[
            "src.audit_logs.router",
            "src.feature_flags.router",
        ]
    )
    register_audit_listeners()
    yield
    app.container.unwire()


def create_app() -> FastAPI:
    """
    Application factory to create and configure the FastAPI app instance.
    """
    container = AppContainer()

    app = FastAPI(
        title="Feature Flag Management Service",
        description="A robust service for managing feature flags with dependency support and automatic audit logging.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.container = container
    db_instance: Database = container.database()
    app.add_middleware(DBSessionMiddleware(db_instance))

    app.include_router(audit_logs_router)
    app.include_router(feature_flags_router)

    @app.get("/", tags=["Root"])
    def read_root():
        return {"status": "ok", "message": "Welcome to the Feature Flag Service!"}

    return app


app = create_app()
