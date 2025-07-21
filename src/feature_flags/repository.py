from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.infrastructure.base_repository import BaseRepository
from .model import FeatureFlag
from .schemas import FeatureFlagCreate, FeatureFlagUpdate


class FeatureFlagRepository(
    BaseRepository[FeatureFlag, FeatureFlagCreate, FeatureFlagUpdate]
):
    async def _get_dependencies_from_ids(
        self, *, dependency_ids: list[int]
    ) -> list[FeatureFlag]:
        if not dependency_ids:
            return []
        statement = select(self.model).where(self.model.id.in_(dependency_ids))
        result = await self.db.execute(statement)
        return result.scalars().all()

    async def get(self, _id: int) -> Optional[FeatureFlag]:
        """
        Retrieves a single flag by its ID, eagerly loading its dependencies
        and dependents to prevent lazy-loading issues in async contexts.
        """
        statement = (
            select(self.model)
            .where(self.model.id == _id)
            .options(
                selectinload(self.model.dependencies),
                selectinload(self.model.dependents),
            )
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, *, name: str) -> Optional[FeatureFlag]:
        """Retrieves a feature flag by its unique name."""
        statement = select(self.model).where(self.model.name == name)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, *, obj_in: FeatureFlagCreate) -> FeatureFlag:
        """
        Overrides the base create method to handle the many-to-many relationship.
        """
        obj_in_data = obj_in.model_dump(exclude={"dependency_ids"})

        db_obj = self.model(**obj_in_data)

        if obj_in.dependency_ids:
            dependencies = await self._get_dependencies_from_ids(
                dependency_ids=obj_in.dependency_ids
            )
            db_obj.dependencies = dependencies

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self, *, db_obj: FeatureFlag, obj_in: FeatureFlagUpdate
    ) -> FeatureFlag:
        """
        Overrides the base update method to handle the many-to-many relationship.
        """
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"dependency_ids"})
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        if obj_in.dependency_ids is not None:
            dependencies = await self._get_dependencies_from_ids(
                dependency_ids=obj_in.dependency_ids
            )
            db_obj.dependencies = dependencies

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
