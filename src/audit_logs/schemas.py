import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AuditLogBase(BaseModel):
    action: str
    actor: Optional[str] = "system"
    details: Optional[dict[str, Any]]
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
    action: Optional[str] = None
    skip: int = 0
    limit: int = 100
