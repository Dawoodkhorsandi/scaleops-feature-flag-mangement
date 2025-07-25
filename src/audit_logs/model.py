from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    JSON,
)
from src.infrastructure.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=True, default="system")
    details = Column(JSON, nullable=True)
    target_entity = Column(String, index=True, nullable=False)
    target_id = Column(String, index=True, nullable=False)
