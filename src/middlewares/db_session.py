from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.infrastructure.database import Database


class DBSessionMiddleware(BaseHTTPMiddleware):
    """
    This middleware ensures that a database session is created for each
    request and properly closed after the request is handled.
    """

    def __init__(self, app, db_manager: Database):
        super().__init__(app)
        self.db_manager = db_manager

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            response = await call_next(request)
        finally:
            await self.db_manager.close_session()
        return response
