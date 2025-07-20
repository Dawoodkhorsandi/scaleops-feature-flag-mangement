from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from src.infrastructure.containers import AppContainer
from . import schemas
from .service import AuditLogService

router = APIRouter(prefix="/history", tags=["Audit Logs"])


@router.get("/", response_model=list[schemas.AuditLog])
@inject
async def get_audit_history(
    query: schemas.AuditLogHistoryQuery = Depends(),
    service: AuditLogService = Depends(Provide[AppContainer.audit_log_service]),
):
    """
    Retrieve the audit history for all operations.

    Supports filtering by `target_entity`, `target_id`, and `action`,
    as well as pagination with `skip` and `limit`.
    """
    return await service.get_history(query=query)
