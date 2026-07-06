from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatType
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers import commands
from db.crud.binding import BindingRepository
from db.models.binding import Binding


def _make_message(
    *,
    chat_type: ChatType = ChatType.SUPERGROUP,
    chat_id: int = -1001234567890,
    user_id: int = 42,
    is_topic: bool = False,
    thread_id: int | None = None,
) -> MagicMock:
    """Build a minimal fake aiogram Message for handler tests."""
    message = MagicMock()
    message.chat.type = chat_type
    message.chat.id = chat_id
    message.from_user.id = user_id
    message.is_topic_message = is_topic
    message.message_thread_id = thread_id
    message.answer = AsyncMock()
    return message


async def _count(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Binding)) or 0


@pytest.mark.anyio
async def test_bind_in_topic_saves_thread_id(
    dbsession: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(commands, "is_chat_admin", AsyncMock(return_value=True))
    message = _make_message(is_topic=True, thread_id=99, chat_id=-100500)

    await commands.cmd_bind(message, bot=MagicMock(), session=dbsession)

    binding = await BindingRepository(dbsession).get_active()
    assert binding is not None
    assert binding.chat_id == -100500
    assert binding.message_thread_id == 99
    message.answer.assert_awaited_once_with(commands._BIND_OK)


@pytest.mark.anyio
async def test_bind_in_regular_chat_saves_null_thread(
    dbsession: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(commands, "is_chat_admin", AsyncMock(return_value=True))
    # A reply in a non-forum group can carry message_thread_id, but is_topic_message
    # is False — so it must be stored as NULL.
    message = _make_message(is_topic=False, thread_id=12345)

    await commands.cmd_bind(message, bot=MagicMock(), session=dbsession)

    binding = await BindingRepository(dbsession).get_active()
    assert binding is not None
    assert binding.message_thread_id is None


@pytest.mark.anyio
async def test_bind_rejects_non_admin(
    dbsession: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(commands, "is_chat_admin", AsyncMock(return_value=False))
    message = _make_message()

    await commands.cmd_bind(message, bot=MagicMock(), session=dbsession)

    assert await _count(dbsession) == 0
    message.answer.assert_awaited_once_with(commands._NOT_ADMIN)


@pytest.mark.anyio
async def test_bind_rejects_private_chat(
    dbsession: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Admin check must not even be reached for a private chat.
    admin_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(commands, "is_chat_admin", admin_mock)
    message = _make_message(chat_type=ChatType.PRIVATE)

    await commands.cmd_bind(message, bot=MagicMock(), session=dbsession)

    assert await _count(dbsession) == 0
    admin_mock.assert_not_called()
    message.answer.assert_awaited_once_with(commands._NOT_GROUP)


@pytest.mark.anyio
async def test_unbind_clears_binding(dbsession: AsyncSession) -> None:
    await BindingRepository(dbsession).set_active(chat_id=1, message_thread_id=None)
    message = _make_message()

    await commands.cmd_unbind(message, session=dbsession)

    assert await _count(dbsession) == 0
    message.answer.assert_awaited_once_with(commands._UNBIND_OK)


@pytest.mark.anyio
async def test_status_reports_current_binding(dbsession: AsyncSession) -> None:
    await BindingRepository(dbsession).set_active(chat_id=777, message_thread_id=5)
    message = _make_message()

    await commands.cmd_status(message, session=dbsession)

    message.answer.assert_awaited_once()
    text = message.answer.await_args.args[0]
    assert "777" in text
    assert "5" in text


@pytest.mark.anyio
async def test_status_when_empty(dbsession: AsyncSession) -> None:
    message = _make_message()
    await commands.cmd_status(message, session=dbsession)
    message.answer.assert_awaited_once_with(commands._STATUS_NONE)
