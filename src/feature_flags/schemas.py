from typing import Optional
from pydantic import BaseModel, Field


class FeatureFlagNested(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class FeatureFlagBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_enabled: bool = False


class FeatureFlagCreate(FeatureFlagBase):
    dependency_ids: list[int] = Field(default_factory=list)


class FeatureFlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    dependency_ids: Optional[list[int]] = Field(default=None)


class FeatureFlag(FeatureFlagBase):
    id: int
    dependencies: list[FeatureFlagNested] = Field(default_factory=list)

    class Config:
        from_attributes = True