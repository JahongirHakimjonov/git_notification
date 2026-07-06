from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bot.instance import get_bot
from bot.setup import setup_bot, shutdown_bot
from core.database import get_db_engine
from core.requests import get_http_transport
from core.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application-scoped resources.

    Startup: eagerly create the DB engine and HTTP transport and, when a bot
    token is configured, register the Telegram webhook + commands.
    Shutdown: delete the webhook, close the bot session, and dispose engines.
    """
    settings = get_settings()
    db_engine = get_db_engine()
    http_transport = get_http_transport()

    bot = None
    if settings.telegram_enabled:
        bot = get_bot()
        await setup_bot(bot)

    yield

    if bot is not None:
        await shutdown_bot(bot)
    await db_engine.dispose()
    await http_transport.aclose()
