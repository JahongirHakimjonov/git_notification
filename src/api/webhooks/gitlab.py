import hmac
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, Request, Response, status
from loguru import logger

from bot.instance import get_bot
from core.settings import get_settings
from services.gitlab.dispatcher import GitLabDispatcher
from services.telegram.notifier import TelegramNotifier

router = APIRouter(prefix="/webhook", tags=["Webhooks"])

_dispatcher = GitLabDispatcher()


def _token_matches(received: str, expected: str) -> bool:
    """Constant-time comparison; a missing/empty configured secret never matches."""
    if not expected:
        return False
    return hmac.compare_digest(received, expected)


async def _deliver(message: str) -> None:
    """Background task: push a formatted message to the active binding."""
    notifier = TelegramNotifier(get_bot())
    await notifier.send(message)


@router.post("/gitlab", summary="Receive GitLab webhook events")
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_gitlab_token: Annotated[str, Header()] = "",
    x_gitlab_event: Annotated[str, Header()] = "",
) -> Response:
    """
    Validate the GitLab secret token, then format and deliver the event.

    Token mismatch -> HTTP 403. Otherwise the event is formatted and delivery is
    handed to a background task so we can return 200 immediately — a slow or
    failing Telegram send must never surface as an error to GitLab (which would
    cause webhook retry storms).
    """
    settings = get_settings()
    if not _token_matches(x_gitlab_token, settings.gitlab_webhook_secret):
        logger.warning("GitLab webhook rejected: invalid X-Gitlab-Token")
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    payload = await request.json()
    logger.debug("GitLab event '{}' received: {}", x_gitlab_event, payload)

    message = _dispatcher.format_event(payload)
    if message is None:
        return Response(status_code=status.HTTP_200_OK)

    if not settings.telegram_enabled:
        logger.warning("Telegram bot not configured; formatted event dropped")
        return Response(status_code=status.HTTP_200_OK)

    background_tasks.add_task(_deliver, message)
    return Response(status_code=status.HTTP_200_OK)
