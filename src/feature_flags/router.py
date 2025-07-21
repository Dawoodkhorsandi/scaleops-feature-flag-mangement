from fastapi import APIRouter, Depends, status
from dependency_injector.wiring import inject, Provide
from pydantic import BaseModel
from src.common.dependencies import set_actor_from_header

from src.infrastructure.containers import AppContainer
from . import schemas
from .service import FeatureFlagService

router = APIRouter(prefix="/flags", tags=["Feature Flags"])


class TogglePayload(BaseModel):
    is_enabled: bool


@router.post(
    "/", response_model=schemas.FeatureFlag, status_code=status.HTTP_201_CREATED
)
@inject
async def create_flag(
    payload: schemas.FeatureFlagCreate,
    _actor_context: None = Depends(set_actor_from_header),
    service: FeatureFlagService = Depends(Provide[AppContainer.feature_flag_service]),
):
    """
    Create a new feature flag.

    - Validates that dependencies exist.
    - Detects and rejects circular dependencies.
    """
    return await service.create(obj_in=payload)


@router.get("/", response_model=list[schemas.FeatureFlag])
@inject
async def get_all_flags(
    skip: int = 0,
    limit: int = 100,
    _actor_context: None = Depends(set_actor_from_header),
    service: FeatureFlagService = Depends(Provide[AppContainer.feature_flag_service]),
):
    """
    Retrieve all feature flags with pagination.
    """
    return await service.get_all(skip=skip, limit=limit)


@router.get("/{flag_id}", response_model=schemas.FeatureFlag)
@inject
async def get_flag(
    flag_id: int,
    _actor_context: None = Depends(set_actor_from_header),
    service: FeatureFlagService = Depends(Provide[AppContainer.feature_flag_service]),
):
    """
    Retrieve the current status and details of a specific flag by its ID.
    """
    return await service.get(_id=flag_id)


@router.patch("/{flag_id}/toggle", response_model=schemas.FeatureFlag)
@inject
async def toggle_flag(
    flag_id: int,
    payload: TogglePayload,
    _actor_context: None = Depends(set_actor_from_header),
    service: FeatureFlagService = Depends(Provide[AppContainer.feature_flag_service]),
):
    """
    Toggle a feature flag ON or OFF.

    - When enabling, verifies that all dependencies are active.
    - When disabling, triggers a cascading disable of all dependent flags.
    """
    return await service.toggle(flag_id=flag_id, is_enabled=payload.is_enabled)


@router.patch("/{flag_id}", response_model=schemas.FeatureFlag)
@inject
async def update_flag(
    flag_id: int,
    payload: schemas.FeatureFlagUpdate,
    _actor_context: None = Depends(set_actor_from_header),
    service: FeatureFlagService = Depends(Provide[AppContainer.feature_flag_service]),
):
    """
    Update a feature flag's properties, including its name, description,
    and dependencies.

    - Validates that new dependencies exist.
    - Detects and rejects circular dependencies.
    """
    return await service.update(flag_id=flag_id, obj_in=payload)
