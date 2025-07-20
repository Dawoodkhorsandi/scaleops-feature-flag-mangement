from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import relationship

from src.infrastructure.database import Base
from ..audit_logs.auditable import Auditable


feature_dependency_association = Table(
    "feature_dependency_association",
    Base.metadata,
    Column("dependent_feature_id", Integer, ForeignKey("feature_flags.id"), primary_key=True),
    Column("parent_feature_id", Integer, ForeignKey("feature_flags.id"), primary_key=True),
)


class FeatureFlag(Base, Auditable):
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=False, nullable=False)

    dependencies = relationship(
        "FeatureFlag",
        secondary=feature_dependency_association,
        primaryjoin=(feature_dependency_association.c.dependent_feature_id == id),
        secondaryjoin=(feature_dependency_association.c.parent_feature_id == id),
        back_populates="dependents",
        lazy="selectin",
    )

    dependents = relationship(
        "FeatureFlag",
        secondary=feature_dependency_association,
        primaryjoin=(feature_dependency_association.c.parent_feature_id == id),
        secondaryjoin=(feature_dependency_association.c.dependent_feature_id == id),
        back_populates="dependencies",
        lazy="selectin",
    )
