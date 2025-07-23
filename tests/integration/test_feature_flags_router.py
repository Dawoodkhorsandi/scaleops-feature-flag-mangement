import pytest
from httpx import AsyncClient


@pytest.fixture
async def headers() -> dict:
    return {"X-Actor": "test-user"}


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


async def test_create_flag_with_dependency(client: AsyncClient, headers: dict):
    parent_res = await client.post(
        "/flags/", json={"name": "Parent Flag"}, headers=headers
    )
    assert parent_res.status_code == 201
    parent_id = parent_res.json()["id"]

    child_res = await client.post(
        "/flags/",
        json={"name": "Child Flag", "dependency_ids": [parent_id]},
        headers=headers,
    )
    assert child_res.status_code == 201
    child_data = child_res.json()
    assert child_data["name"] == "Child Flag"
    assert len(child_data["dependencies"]) == 1
    assert child_data["dependencies"][0]["id"] == parent_id


async def test_create_flag_name_conflict(client: AsyncClient, headers: dict):
    """Test that creating a flag with a duplicate name fails."""
    await client.post("/flags/", json={"name": "Duplicate Name"}, headers=headers)
    response = await client.post(
        "/flags/", json={"name": "Duplicate Name"}, headers=headers
    )
    assert response.status_code == 409  # Conflict
    assert "already exists" in response.json()["detail"]


async def test_toggle_flag_on_fails_if_dependency_is_off(
    client: AsyncClient, headers: dict
):
    """Test that a flag cannot be enabled if its dependency is disabled."""
    parent_res = await client.post(
        "/flags/", json={"name": "Parent Off"}, headers=headers
    )
    parent_id = parent_res.json()["id"]

    child_res = await client.post(
        "/flags/",
        json={"name": "Child Off", "dependency_ids": [parent_id]},
        headers=headers,
    )
    child_id = child_res.json()["id"]

    # Try to enable the child flag
    toggle_res = await client.patch(
        f"/flags/{child_id}/toggle", json={"is_enabled": True}, headers=headers
    )
    assert toggle_res.status_code == 400  # Bad Request
    assert "Missing active dependencies" in toggle_res.json()["detail"]


async def test_toggle_flag_off_cascades_to_dependents(
    client: AsyncClient, headers: dict
):
    """Test that disabling a parent flag also disables its dependent flags."""
    parent_res = await client.post(
        "/flags/", json={"name": "Cascading Parent"}, headers=headers
    )
    parent_id = parent_res.json()["id"]
    await client.patch(
        f"/flags/{parent_id}/toggle", json={"is_enabled": True}, headers=headers
    )

    child_res = await client.post(
        "/flags/",
        json={"name": "Cascading Child", "dependency_ids": [parent_id]},
        headers=headers,
    )
    child_id = child_res.json()["id"]
    await client.patch(
        f"/flags/{child_id}/toggle", json={"is_enabled": True}, headers=headers
    )

    disable_res = await client.patch(
        f"/flags/{parent_id}/toggle", json={"is_enabled": False}, headers=headers
    )
    assert disable_res.status_code == 200
    assert disable_res.json()["is_enabled"] is False

    child_check_res = await client.get(f"/flags/{child_id}", headers=headers)
    assert child_check_res.status_code == 200
    assert child_check_res.json()["is_enabled"] is False


async def test_get_all_flags(client: AsyncClient, headers: dict):
    """Test retrieving all flags."""
    await client.post("/flags/", json={"name": "Flag A"}, headers=headers)
    await client.post("/flags/", json={"name": "Flag B"}, headers=headers)

    response = await client.get("/flags/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
