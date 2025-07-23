from typing import Set

from .repository import FeatureFlagRepository
from . import schemas, model

from .exceptions import (
    SelfDependencyException,
    FeatureFlagNotFoundException,
    FeatureFlagConflictException,
    CircularDependencyException,
    MissingDependenciesException,
)
from src.audit_logs.decorators import with_audit_action
from .enums import FeatureFlagAuditActionEnum


class FeatureFlagService:
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
            raise SelfDependencyException()

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
                    raise CircularDependencyException(flag_name=dep.name)
                if dep.id not in path:
                    await dfs(dep.id)

            visiting.remove(node_id)

        for dep_id in dependency_ids:
            if dep_id not in path:
                await dfs(dep_id)

    @with_audit_action(FeatureFlagAuditActionEnum.CREATE)
    async def create(self, *, obj_in: schemas.FeatureFlagCreate) -> model.FeatureFlag:
        """Creates a new feature flag after validating its name and dependencies."""
        if await self.repository.get_by_name(name=obj_in.name):
            raise FeatureFlagConflictException(
                f"Feature flag with name '{obj_in.name}' already exists."
            )

        if obj_in.dependency_ids:
            deps = await self.repository._get_dependencies_from_ids(
                dependency_ids=obj_in.dependency_ids
            )
            if len(deps) != len(set(obj_in.dependency_ids)):
                raise FeatureFlagNotFoundException(
                    "One or more dependency IDs not found."
                )
        await self._validate_circular_dependency(
            flag_id=None, dependency_ids=obj_in.dependency_ids
        )

        return await self.repository.create(obj_in=obj_in)

    @with_audit_action(FeatureFlagAuditActionEnum.TOGGLE)
    async def toggle(self, *, flag_id: int, is_enabled: bool) -> model.FeatureFlag:
        """Toggles a flag's state, handling all dependency rules."""
        db_flag = await self.repository.get(_id=flag_id)
        if not db_flag:
            raise FeatureFlagNotFoundException()
        if is_enabled:
            missing_deps = [
                dep.name for dep in db_flag.dependencies if not dep.is_enabled
            ]
            if missing_deps:
                raise MissingDependenciesException(missing_dependencies=missing_deps)
            updated_flag = await self.repository.update(
                db_obj=db_flag, obj_in=schemas.FeatureFlagUpdate(is_enabled=is_enabled)
            )

        else:
            updated_flag = await self.repository.update(
                db_obj=db_flag, obj_in=schemas.FeatureFlagUpdate(is_enabled=is_enabled)
            )

            await self._cascade_disable(db_flag)

        return updated_flag

    @with_audit_action(FeatureFlagAuditActionEnum.AUTO_DISABLE)
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
            raise FeatureFlagNotFoundException()
        return flag

    async def get_all(self, *, skip: int, limit: int) -> list[model.FeatureFlag]:
        """Retrieves a paginated list of all feature flags."""
        return await self.repository.get_all(skip=skip, limit=limit)

    @with_audit_action(FeatureFlagAuditActionEnum.UPDATE)
    async def update(
        self, *, flag_id: int, obj_in: schemas.FeatureFlagUpdate
    ) -> model.FeatureFlag:
        db_flag = await self.repository.get(_id=flag_id)
        if not db_flag:
            raise FeatureFlagNotFoundException()

        if obj_in.name and obj_in.name != db_flag.name:
            if await self.repository.get_by_name(name=obj_in.name):
                raise FeatureFlagConflictException(
                    f"Feature flag with name '{obj_in.name}' already exists."
                )

        if obj_in.dependency_ids is not None:
            await self._validate_circular_dependency(
                flag_id=flag_id, dependency_ids=obj_in.dependency_ids
            )

        return await self.repository.update(db_obj=db_flag, obj_in=obj_in)
