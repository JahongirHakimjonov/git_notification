import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud.binding import BindingRepository
from db.models.binding import Binding


@pytest.mark.anyio
async def test_get_active_returns_none_when_empty(dbsession: AsyncSession) -> None:
    assert await BindingRepository(dbsession).get_active() is None


@pytest.mark.anyio
async def test_set_active_keeps_only_one_binding(dbsession: AsyncSession) -> None:
    repo = BindingRepository(dbsession)
    await repo.set_active(chat_id=111, message_thread_id=None)
    await repo.set_active(chat_id=222, message_thread_id=9)

    active = await repo.get_active()
    assert active is not None
    assert active.chat_id == 222
    assert active.message_thread_id == 9

    count = await dbsession.scalar(select(func.count()).select_from(Binding))
    assert count == 1


@pytest.mark.anyio
async def test_set_active_stores_regular_chat_without_thread(dbsession: AsyncSession) -> None:
    repo = BindingRepository(dbsession)
    binding = await repo.set_active(chat_id=-100500, message_thread_id=None)
    assert binding.message_thread_id is None
    assert binding.created_at is not None


@pytest.mark.anyio
async def test_clear_removes_binding(dbsession: AsyncSession) -> None:
    repo = BindingRepository(dbsession)
    await repo.set_active(chat_id=111, message_thread_id=None)

    assert await repo.clear() is True
    assert await repo.get_active() is None
    # Clearing again reports nothing was removed.
    assert await repo.clear() is False
