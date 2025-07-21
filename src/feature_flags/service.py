from typing import Set
from sqlalchemy import select

from .repository import FeatureFlagRepository
from . import schemas, model
from ..common.exceptions import (
    ConflictException,
    NotFoundException,
    BadRequestException,
)


class FeatureFlagService:
    """
    Handles the business logic for feature flags, including dependency validation
    and cascading state changes.
    """

    def __init__(self, repository: FeatureFlagRepository):
        self.repository = repository

    async def _validate_circular_dependency(
        self, flag_id: int | None, dependency_ids: list[int]
    ):
        """
        Performs a Depth-First Search (DFS) to detect cycles in the dependency graph.
        """
        if not dependency_ids:
            return

        if flag_id and flag_id in dependency_ids:
            raise BadRequestException("A feature flag cannot depend on itself.")

        path: Set[int] = set([flag_id]) if flag_id else set()
        visiting: Set[int] = set([flag_id]) if flag_id else set()

        async def dfs(node_id: int):
            path.add(node_id)
            visiting.add(node_id)

            node = await self.repository.get(node_id)
            if not node:
                return

            for dep in node.dependencies:
                if dep.id in visiting:
                    raise BadRequestException(
                        f"Circular dependency detected with flag '{dep.name}'."
                    )
                if dep.id not in path:
                    await dfs(dep.id)

            visiting.remove(node_id)

        for dep_id in dependency_ids:
            if dep_id not in path:
                await dfs(dep_id)

    async def create(self, *, obj_in: schemas.FeatureFlagCreate) -> model.FeatureFlag:
        """Creates a new feature flag after validating its name and dependencies."""
        if await self.repository.get_by_name(name=obj_in.name):
            raise ConflictException(
                f"Feature flag with name '{obj_in.name}' already exists."
            )

        if obj_in.dependency_ids:
            deps = await self.repository._get_dependencies_from_ids(
                dependency_ids=obj_in.dependency_ids
            )
            if len(deps) != len(set(obj_in.dependency_ids)):
                raise NotFoundException("One or more dependency IDs not found.")

        await self._validate_circular_dependency(
            flag_id=None, dependency_ids=obj_in.dependency_ids
        )

        return await self.repository.create(obj_in=obj_in)

    async def toggle(self, *, flag_id: int, is_enabled: bool) -> model.FeatureFlag:
        """Toggles a flag's state, handling all dependency rules."""
        db_flag = await self.repository.get(_id=flag_id)
        if not db_flag:
            raise NotFoundException("Feature flag not found.")

        if is_enabled:
            # When enabling, check if all dependencies are already active.
            missing_deps = [
                dep.name for dep in db_flag.dependencies if not dep.is_enabled
            ]
            if missing_deps:
                raise BadRequestException(
                    f"Cannot enable. Missing active dependencies: {', '.join(missing_deps)}"
                )
        else:
            # When disabling, trigger a cascading disable for all dependents.
            await self._cascade_disable(db_flag)

        # The automatic audit system will log this update and all cascading updates.
        return await self.repository.update(
            db_obj=db_flag, obj_in=schemas.FeatureFlagUpdate(is_enabled=is_enabled)
        )

    async def _cascade_disable(self, parent_flag: model.FeatureFlag):
        """Iteratively disables all flags that depend on the parent flag."""
        flags_to_process = list(parent_flag.dependents)
        while flags_to_process:
            dependent_flag = flags_to_process.pop(0)
            if dependent_flag.is_enabled:
                await self.repository.update(
                    db_obj=dependent_flag,
                    obj_in=schemas.FeatureFlagUpdate(is_enabled=False),
                )
                flags_to_process.extend(dependent_flag.dependents)

    async def get(self, _id: int) -> model.FeatureFlag:
        """Retrieves a single flag by its ID."""
        flag = await self.repository.get(_id)
        if not flag:
            raise NotFoundException("Feature flag not found.")
        return flag

    async def get_all(self, *, skip: int, limit: int) -> list[model.FeatureFlag]:
        """Retrieves a paginated list of all feature flags."""
        return await self.repository.get_all(skip=skip, limit=limit)

    async def update(
        self, *, flag_id: int, obj_in: schemas.FeatureFlagUpdate
    ) -> model.FeatureFlag:
        """
        Updates a feature flag's properties, ensuring data integrity and
        preventing the introduction of dependency cycles.
        """
        db_flag = await self.repository.get(_id=flag_id)
        if not db_flag:
            raise NotFoundException("Feature flag not found.")

        if obj_in.name and obj_in.name != db_flag.name:
            if await self.repository.get_by_name(name=obj_in.name):
                raise ConflictException(
                    f"Feature flag with name '{obj_in.name}' already exists."
                )

        if obj_in.dependency_ids is not None:
            await self._validate_circular_dependency(
                flag_id=flag_id, dependency_ids=obj_in.dependency_ids
            )

        return await self.repository.update(db_obj=db_flag, obj_in=obj_in)
