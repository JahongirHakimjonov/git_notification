import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError, TelegramRetryAfter
from loguru import logger

from core.database import get_session_factory
from db.crud.binding import BindingRepository

# Retry policy for transient network failures (avoid magic numbers).
MAX_SEND_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.0


class TelegramNotifier:
    """
    Delivers a rendered notification to the active :class:`Binding`.

    Looks up where notifications are bound, then sends the HTML message to that
    chat (and forum Topic, if any). Parse mode and link-preview settings come
    from the bot's :class:`DefaultBotProperties`. Failures are logged and
    swallowed — callers (the GitLab webhook) must never surface a Telegram error
    back to GitLab, which would trigger webhook retry storms.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send(self, html: str) -> bool:
        """
        Send ``html`` to the active binding.

        :param html: fully rendered Telegram HTML message.
        :return: ``True`` if delivered, ``False`` if no binding or send failed.
        """
        async with get_session_factory()() as session:
            binding = await BindingRepository(session).get_active()

        if binding is None:
            logger.warning("No active binding configured; notification dropped")
            return False

        return await self._send_with_retry(
            chat_id=binding.chat_id,
            message_thread_id=binding.message_thread_id,
            html=html,
        )

    async def _send_with_retry(self, chat_id: int, message_thread_id: int | None, html: str) -> bool:
        """Send with bounded retries for transient (network / rate-limit) errors."""
        for attempt in range(1, MAX_SEND_ATTEMPTS + 1):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=html,
                    message_thread_id=message_thread_id,
                )
            except TelegramRetryAfter as error:
                logger.warning("Rate limited by Telegram; retrying after {}s", error.retry_after)
                await asyncio.sleep(error.retry_after)
            except TelegramNetworkError as error:
                logger.warning(
                    "Telegram network error (attempt {}/{}): {}",
                    attempt,
                    MAX_SEND_ATTEMPTS,
                    error,
                )
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
            except TelegramAPIError:
                # Non-retryable API error (bad chat_id, bot kicked, bad HTML, ...).
                logger.exception("Telegram API error; giving up on this notification")
                return False
            else:
                logger.info(
                    "Notification delivered to chat_id={} thread_id={}",
                    chat_id,
                    message_thread_id,
                )
                return True

        logger.error("Failed to deliver notification after {} attempts", MAX_SEND_ATTEMPTS)
        return False
