import pytest
from httpx import AsyncClient


@pytest.fixture
async def headers() -> dict:
    return {"X-Actor": "audit-tester"}


async def test_get_audit_history_after_actions(client: AsyncClient, headers: dict):
    create_res = await client.post(
        "/flags/", json={"name": "Audited Flag"}, headers=headers
    )
    assert create_res.status_code == 201
    flag_id = create_res.json()["id"]

    toggle_res = await client.patch(
        f"/flags/{flag_id}/toggle", json={"is_enabled": True}, headers=headers
    )
    assert toggle_res.status_code == 200

    history_res = await client.get("/history/", headers=headers)
    assert history_res.status_code == 200
    history_data = history_res.json()

    assert len(history_data) == 2
    assert history_data[0]["action"] == "toggle"
    assert history_data[0]["target_id"] == str(flag_id)
    assert history_data[0]["actor"] == "audit-tester"

    assert history_data[1]["action"] == "create"
    assert history_data[1]["target_id"] == str(flag_id)


async def test_get_audit_history_with_filters(client: AsyncClient, headers: dict):
    res1 = await client.post("/flags/", json={"name": "Flag One"}, headers=headers)
    flag1_id = res1.json()["id"]

    res2 = await client.post("/flags/", json={"name": "Flag Two"}, headers=headers)
    flag2_id = res2.json()["id"]

    params = {"target_entity": "feature_flags", "target_id": str(flag2_id)}
    history_res = await client.get("/history/", params=params, headers=headers)

    assert history_res.status_code == 200
    history_data = history_res.json()

    assert len(history_data) == 1
    assert history_data[0]["target_id"] == str(flag2_id)
    assert history_data[0]["action"] == "create"
