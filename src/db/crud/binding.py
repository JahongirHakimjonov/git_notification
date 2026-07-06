from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.dependencies import get_db_session
from db.models.binding import Binding


class BindingRepository:
    """
    Data-access for the single active notification :class:`Binding`.

    The domain rule is "exactly one active binding": ``set_active`` deletes any
    existing rows and inserts the new one inside the caller's transaction, so the
    table never holds more than one binding. Usable both as a FastAPI dependency
    (``Depends()``) and directly with an explicit session (bot middleware /
    background notifier).
    """

    def __init__(self, session: AsyncSession = Depends(get_db_session)) -> None:
        self.session = session

    async def get_active(self) -> Binding | None:
        """Return the current binding, or ``None`` if nothing is bound."""
        result = await self.session.execute(select(Binding).order_by(Binding.id.desc()).limit(1))
        return result.scalar_one_or_none()

    async def set_active(self, chat_id: int, message_thread_id: int | None) -> Binding:
        """
        Replace any existing binding with a new one.

        :param chat_id: Telegram chat ID to deliver notifications to.
        :param message_thread_id: forum Topic ID, or ``None`` for a regular chat.
        :return: the newly created binding.
        """
        await self.session.execute(delete(Binding))
        binding = Binding(chat_id=chat_id, message_thread_id=message_thread_id)
        self.session.add(binding)
        await self.session.flush()
        return binding

    async def clear(self) -> bool:
        """
        Remove the active binding, if any.

        :return: ``True`` if a binding was removed, ``False`` if none existed.
        """
        result = await self.session.execute(delete(Binding))
        return bool(result.rowcount)
