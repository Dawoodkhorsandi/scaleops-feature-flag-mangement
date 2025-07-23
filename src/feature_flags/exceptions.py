from src.common.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)


class FeatureFlagException(Exception):
    pass


class FeatureFlagNotFoundException(NotFoundException, FeatureFlagException):
    def __init__(self, message: str = "Feature flag not found."):
        super().__init__(message=message)


class FeatureFlagConflictException(ConflictException, FeatureFlagException):
    def __init__(self, message: str = "Feature flag conflict."):
        super().__init__(message=message)


class FeatureFlagBadRequestException(BadRequestException, FeatureFlagException):
    def __init__(self, message: str = "Invalid feature flag request."):
        super().__init__(message=message)


class SelfDependencyException(FeatureFlagBadRequestException):
    def __init__(self):
        super().__init__(message="A feature flag cannot depend on itself.")


class CircularDependencyException(FeatureFlagBadRequestException):
    def __init__(self, flag_name: str):
        super().__init__(
            message=f"Circular dependency detected involving flag '{flag_name}'."
        )


class MissingDependenciesException(FeatureFlagBadRequestException):
    def __init__(self, missing_dependencies: list[str]):
        self.missing_dependencies = missing_dependencies
        super().__init__(message="Cannot enable due to inactive dependencies.")
