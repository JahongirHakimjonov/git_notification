from functools import cache

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from loguru import logger

from bot.handlers.commands import router as commands_router
from bot.middlewares import DatabaseMiddleware
from core.settings import get_settings

# Only message updates are handled, so we subscribe to just those.
ALLOWED_UPDATES = ["message"]

BOT_COMMANDS = [
    BotCommand(command="bind", description="Notifikatsiyani shu joyga bog'lash (admin)"),
    BotCommand(command="unbind", description="Bog'lanishni bekor qilish"),
    BotCommand(command="status", description="Joriy bog'lanishni ko'rsatish"),
    BotCommand(command="help", description="Yordam"),
]


@cache
def get_dispatcher() -> Dispatcher:
    """Return the singleton :class:`Dispatcher` with routers and middleware wired."""
    dispatcher = Dispatcher()
    dispatcher.message.middleware(DatabaseMiddleware())
    dispatcher.include_router(commands_router)
    return dispatcher


async def setup_bot(bot: Bot) -> None:
    """
    Register commands and the Telegram webhook on startup.

    When ``TELEGRAM_WEBHOOK_URL`` is not configured, the webhook is left
    unregistered (so the service still boots — useful for local testing without
    a public URL). Commands are always published.
    """
    settings = get_settings()
    await bot.set_my_commands(BOT_COMMANDS)

    if not settings.telegram_webhook_url:
        logger.warning("TELEGRAM_WEBHOOK_URL is not set; Telegram webhook was NOT registered")
        return

    await bot.set_webhook(
        url=settings.telegram_webhook_full_url,
        secret_token=settings.telegram_webhook_secret or None,
        allowed_updates=ALLOWED_UPDATES,
        drop_pending_updates=True,
    )
    logger.info("Telegram webhook registered at {}", settings.telegram_webhook_full_url)


async def shutdown_bot(bot: Bot) -> None:
    """Delete the webhook (if any) and close the bot session on shutdown."""
    settings = get_settings()
    try:
        if settings.telegram_webhook_url:
            await bot.delete_webhook(drop_pending_updates=False)
            logger.info("Telegram webhook deleted")
    finally:
        await bot.session.close()
