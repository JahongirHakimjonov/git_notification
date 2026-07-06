from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramNetworkError

from db.crud.binding import BindingRepository
from services.telegram import notifier as notifier_module
from services.telegram.notifier import TelegramNotifier


class _FakeSession:
    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *args: object) -> bool:
        return False


def _patch_binding(monkeypatch: pytest.MonkeyPatch, binding: object) -> None:
    """Make the notifier's internal session lookup return ``binding`` without a DB."""
    monkeypatch.setattr(notifier_module, "get_session_factory", lambda: (lambda: _FakeSession()))

    async def _get_active(self: BindingRepository) -> object:
        return binding

    monkeypatch.setattr(BindingRepository, "get_active", _get_active)


@pytest.mark.anyio
async def test_send_includes_thread_id_for_topic(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_binding(monkeypatch, MagicMock(chat_id=123, message_thread_id=7))
    bot = AsyncMock()
    result = await TelegramNotifier(bot).send("<b>hi</b>")

    assert result is True
    bot.send_message.assert_awaited_once_with(chat_id=123, text="<b>hi</b>", message_thread_id=7)


@pytest.mark.anyio
async def test_send_omits_thread_id_for_regular_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_binding(monkeypatch, MagicMock(chat_id=555, message_thread_id=None))
    bot = AsyncMock()
    result = await TelegramNotifier(bot).send("<b>hi</b>")

    assert result is True
    bot.send_message.assert_awaited_once_with(chat_id=555, text="<b>hi</b>", message_thread_id=None)


@pytest.mark.anyio
async def test_send_returns_false_when_no_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_binding(monkeypatch, None)
    bot = AsyncMock()
    result = await TelegramNotifier(bot).send("<b>hi</b>")

    assert result is False
    bot.send_message.assert_not_called()


@pytest.mark.anyio
async def test_send_retries_transient_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notifier_module.asyncio, "sleep", AsyncMock())
    bot = AsyncMock()
    bot.send_message.side_effect = [TelegramNetworkError(method=MagicMock(), message="boom"), None]

    result = await TelegramNotifier(bot)._send_with_retry(chat_id=1, message_thread_id=None, html="x")

    assert result is True
    assert bot.send_message.await_count == 2
