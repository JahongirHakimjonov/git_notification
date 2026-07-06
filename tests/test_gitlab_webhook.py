import pytest
from httpx import AsyncClient

from api.webhooks import gitlab as gitlab_module
from core.settings import get_settings
from tests import payloads

# Matches GITLAB_WEBHOOK_SECRET in .env.test / .env.ci.
SECRET = "test-gitlab-secret"


@pytest.mark.anyio
async def test_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/webhook/gitlab",
        json=payloads.PUSH,
        headers={"X-Gitlab-Token": "wrong-secret"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_rejects_missing_token(client: AsyncClient) -> None:
    response = await client.post("/webhook/gitlab", json=payloads.PUSH)
    assert response.status_code == 403


@pytest.mark.anyio
async def test_accepts_valid_push(client: AsyncClient) -> None:
    response = await client.post(
        "/webhook/gitlab",
        json=payloads.PUSH,
        headers={"X-Gitlab-Token": SECRET, "X-Gitlab-Event": "Push Hook"},
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_ignored_event_still_returns_200(client: AsyncClient) -> None:
    # A comment on an Issue is not delivered, but the webhook must still 200.
    response = await client.post(
        "/webhook/gitlab",
        json=payloads.NOTE_ISSUE,
        headers={"X-Gitlab-Token": SECRET, "X-Gitlab-Event": "Note Hook"},
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_valid_event_schedules_delivery(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Enable the bot (property reads the token) and capture the background deliver.
    monkeypatch.setattr(get_settings(), "telegram_bot_token", "TESTTOKEN")
    delivered: dict[str, str] = {}

    async def fake_deliver(message: str) -> None:
        delivered["message"] = message

    monkeypatch.setattr(gitlab_module, "_deliver", fake_deliver)

    response = await client.post(
        "/webhook/gitlab",
        json=payloads.MERGE_REQUEST_MERGED,
        headers={"X-Gitlab-Token": SECRET, "X-Gitlab-Event": "Merge Request Hook"},
    )
    assert response.status_code == 200
    assert "Merge Completed" in delivered["message"]
