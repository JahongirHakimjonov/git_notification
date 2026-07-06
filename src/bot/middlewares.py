from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from core.database import get_session_factory


class DatabaseMiddleware(BaseMiddleware):
    """
    Provides an :class:`AsyncSession` to handlers under the ``session`` key.

    Mirrors the FastAPI ``get_db_session`` dependency: commits when the handler
    succeeds, rolls back on exception, and always closes the session.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with get_session_factory()() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()
                return result
