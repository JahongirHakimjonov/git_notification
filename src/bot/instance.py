from functools import cache

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from core.settings import get_settings


@cache
def get_bot() -> Bot:
    """
    Return the singleton aiogram :class:`Bot`.

    Parse mode (HTML) and link-preview suppression are baked into the bot's
    defaults, so message senders need not repeat them. Raises if no token is
    configured — callers must guard with ``settings.telegram_enabled`` first.
    """
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    session = AiohttpSession(timeout=settings.telegram_request_timeout)
    return Bot(
        token=settings.telegram_bot_token,
        session=session,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )
