import pytest
from httpx import AsyncClient

from src.common.context import actor_context
from src.feature_flags.repository import FeatureFlagRepository
from src.feature_flags.schemas import FeatureFlagCreate, FeatureFlagUpdate


@pytest.fixture
async def headers() -> dict:
    actor_id = "test-user"
    actor_context.set(actor_id)
    return {"X-Actor": actor_id}


async def test_create_flag_success(client: AsyncClient, headers: dict):
    response = await client.post(
        "/flags/",
        json={"name": "New Feature", "description": "A cool new feature"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Feature"
    assert data["is_enabled"] is False
    assert "id" in data


async def test_create_flag_with_dependency(
    client: AsyncClient, headers: dict, feature_flag_repo: FeatureFlagRepository
):
    parent_flag = await feature_flag_repo.create(
        obj_in=FeatureFlagCreate(name="Parent Flag")
    )

    child_res = await client.post(
        "/flags/",
        json={"name": "Child Flag", "dependency_ids": [parent_flag.id]},
        headers=headers,
    )

    assert child_res.status_code == 201
    child_data = child_res.json()
    assert child_data["name"] == "Child Flag"
    assert len(child_data["dependencies"]) == 1
    assert child_data["dependencies"][0]["id"] == parent_flag.id


async def test_create_flag_name_conflict(
    client: AsyncClient, headers: dict, feature_flag_repo: FeatureFlagRepository
):
    await feature_flag_repo.create(obj_in=FeatureFlagCreate(name="Duplicate Name"))

    response = await client.post(
        "/flags/", json={"name": "Duplicate Name"}, headers=headers
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


async def test_toggle_flag_on_fails_if_dependency_is_off(
    client: AsyncClient, headers: dict, feature_flag_repo: FeatureFlagRepository
):
    parent_flag = await feature_flag_repo.create(
        obj_in=FeatureFlagCreate(name="Parent Off")
    )
    child_flag = await feature_flag_repo.create(
        obj_in=FeatureFlagCreate(name="Child Off", dependency_ids=[parent_flag.id])
    )

    toggle_res = await client.patch(
        f"/flags/{child_flag.id}/toggle", json={"is_enabled": True}, headers=headers
    )

    assert toggle_res.status_code == 400
    assert "Cannot enable due to inactive dependencies." in toggle_res.json()["detail"]


async def test_toggle_flag_off_cascades_to_dependents(
    client: AsyncClient, headers: dict, feature_flag_repo: FeatureFlagRepository
):
    parent_flag = await feature_flag_repo.create(
        obj_in=FeatureFlagCreate(name="Cascading Parent")
    )
    parent_flag = await feature_flag_repo.update(
        db_obj=parent_flag, obj_in=FeatureFlagUpdate(is_enabled=True)
    )

    child_flag = await feature_flag_repo.create(
        obj_in=FeatureFlagCreate(
            name="Cascading Child", dependency_ids=[parent_flag.id]
        )
    )
    await feature_flag_repo.update(
        db_obj=child_flag, obj_in=FeatureFlagUpdate(is_enabled=True)
    )

    disable_res = await client.patch(
        f"/flags/{parent_flag.id}/toggle", json={"is_enabled": False}, headers=headers
    )

    assert disable_res.status_code == 200
    assert disable_res.json()["is_enabled"] is False

    updated_child = await feature_flag_repo.get(child_flag.id)
    assert updated_child is not None
    assert updated_child.is_enabled is False


async def test_get_all_flags(
    client: AsyncClient, headers: dict, feature_flag_repo: FeatureFlagRepository
):
    await feature_flag_repo.create(obj_in=FeatureFlagCreate(name="Flag A"))
    await feature_flag_repo.create(obj_in=FeatureFlagCreate(name="Flag B"))

    response = await client.get("/flags/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert {d["name"] for d in data} == {"Flag A", "Flag B"}


async def test_create_flag_with_nonexistent_dependency(
    client: AsyncClient, headers: dict
):
    response = await client.post(
        "/flags/",
        json={"name": "Lonely Flag", "dependency_ids": [9999]},
        headers=headers,
    )
    assert response.status_code == 404
    assert "One or more dependency IDs not found" in response.json()["detail"]


async def test_update_flag_circular_dependency(
    client: AsyncClient, headers: dict, feature_flag_repo: FeatureFlagRepository
):
    flag_a = await feature_flag_repo.create(obj_in=FeatureFlagCreate(name="Flag A"))
    await feature_flag_repo.create(
        obj_in=FeatureFlagCreate(name="Flag B", dependency_ids=[flag_a.id])
    )

    response = await client.patch(
        f"/flags/{flag_a.id}",
        json={"dependency_ids": [2]},
        headers=headers,
    )

    assert response.status_code == 400
    assert "Circular dependency detected" in response.json()["detail"]


async def test_get_single_flag_not_found(client: AsyncClient, headers: dict):
    response = await client.get("/flags/9999", headers=headers)
    assert response.status_code == 404


async def test_update_flag_properties_success(
    client: AsyncClient, headers: dict, feature_flag_repo: FeatureFlagRepository
):
    flag = await feature_flag_repo.create(
        obj_in=FeatureFlagCreate(name="Original Name")
    )

    response = await client.patch(
        f"/flags/{flag.id}",
        json={"name": "Updated Name", "description": "New description"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "New description"


async def test_update_flag_to_conflicting_name(
    client: AsyncClient, headers: dict, feature_flag_repo: FeatureFlagRepository
):

    await feature_flag_repo.create(obj_in=FeatureFlagCreate(name="Existing Name"))
    flag_to_update = await feature_flag_repo.create(
        obj_in=FeatureFlagCreate(name="Original Name")
    )

    response = await client.patch(
        f"/flags/{flag_to_update.id}",
        json={"name": "Existing Name"},
        headers=headers,
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
