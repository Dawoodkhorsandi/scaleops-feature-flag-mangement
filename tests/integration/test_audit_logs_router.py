import pytest
from httpx import AsyncClient
from src.feature_flags.repository import FeatureFlagRepository
from src.feature_flags.schemas import FeatureFlagCreate, FeatureFlagUpdate
from src.common.context import actor_context


@pytest.fixture
async def headers() -> dict:
    actor_id = "audit-tester"
    actor_context.set(actor_id)
    return {"X-Actor": actor_id}


async def test_get_audit_history_after_actions(
    client: AsyncClient,
    headers: dict,
    feature_flag_repo: FeatureFlagRepository,
):
    flag = await feature_flag_repo.create(obj_in=FeatureFlagCreate(name="Audited Flag"))
    await feature_flag_repo.update(
        db_obj=flag, obj_in=FeatureFlagUpdate(description="New Description")
    )

    history_res = await client.get("/history/", headers=headers)

    assert history_res.status_code == 200
    history_data = history_res.json()

    assert len(history_data) == 2
    assert history_data[0]["action"] == "UPDATE"
    assert history_data[0]["target_id"] == str(flag.id)
    assert history_data[0]["actor"] == "audit-tester"

    assert history_data[1]["action"] == "CREATE"
    assert history_data[1]["target_id"] == str(flag.id)
    assert history_data[1]["actor"] == "audit-tester"


async def test_get_audit_history_with_filters(
    client: AsyncClient,
    headers: dict,
    feature_flag_repo: FeatureFlagRepository,
):
    await feature_flag_repo.create(obj_in=FeatureFlagCreate(name="Flag One"))
    flag2 = await feature_flag_repo.create(obj_in=FeatureFlagCreate(name="Flag Two"))

    params = {"target_entity": "feature_flags", "target_id": str(flag2.id)}
    history_res = await client.get("/history/", params=params, headers=headers)

    assert history_res.status_code == 200
    history_data = history_res.json()

    assert len(history_data) == 1
    assert history_data[0]["target_id"] == str(flag2.id)
    assert history_data[0]["action"] == "CREATE"
