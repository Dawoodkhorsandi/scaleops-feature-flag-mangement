import datetime
from typing import Any, Optional

from pydantic import BaseModel


from .model import AuditAction


class AuditLogBase(BaseModel):
    action: AuditAction
    actor: Optional[str] = "system"
    details: Optional[dict[str, Any]] = None
    target_entity: str
    target_id: str


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


class AuditLogHistoryQuery(BaseModel):
    target_entity: Optional[str] = None
    target_id: Optional[str] = None
    action: Optional[AuditAction] = None
    skip: int = 0
    limit: int = 100
