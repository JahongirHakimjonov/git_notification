import hmac
from typing import Annotated

from aiogram.types import Update
from fastapi import APIRouter, Header, Request, Response, status
from loguru import logger

from bot.instance import get_bot
from bot.setup import get_dispatcher
from core.settings import get_settings

router = APIRouter(prefix="/webhook", tags=["Webhooks"])


@router.post("/telegram", summary="Receive Telegram bot updates")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[str, Header()] = "",
) -> Response:
    """
    Feed an incoming Telegram update into the aiogram dispatcher.

    When a webhook secret is configured, the ``X-Telegram-Bot-Api-Secret-Token``
    header must match (else HTTP 403). Returns 503 when the bot is not
    configured so callers get an explicit, non-silent signal.
    """
    settings = get_settings()

    if settings.telegram_webhook_secret and not hmac.compare_digest(
        x_telegram_bot_api_secret_token,
        settings.telegram_webhook_secret,
    ):
        logger.warning("Telegram webhook rejected: invalid secret token")
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    if not settings.telegram_enabled:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    bot = get_bot()
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await get_dispatcher().feed_update(bot, update)
    return Response(status_code=status.HTTP_200_OK)
