from aiogram import Bot, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters import is_chat_admin
from db.crud.binding import BindingRepository

router = Router(name="commands")

# Chat types where /bind may be used.
_GROUP_TYPES = (ChatType.GROUP, ChatType.SUPERGROUP)

HELP_TEXT = (
    "🤖 <b>GitLab → Telegram Notifier</b>\n\n"
    "Mavjud buyruqlar:\n\n"
    "/bind — Ushbu chat yoki Topic'ni notifikatsiyalarga bog'laydi (faqat admin).\n"
    "/unbind — Bog'lanishni bekor qiladi.\n"
    "/status — Joriy bog'lanish ma'lumotini ko'rsatadi.\n"
    "/help — Ushbu yordam xabarini ko'rsatadi.\n\n"
    "GitLab webhook eventlari (Push, Merge Request, Pipeline, Job, Tag, Release, "
    "Note) shu joyga yuboriladi."
)

_NOT_GROUP = "❗️ Bu buyruq faqat guruh yoki Topic ichida ishlaydi."
_NOT_ADMIN = "🚫 Bu buyruqni faqat guruh administratori ishlata oladi."
_BIND_OK = "✅ Notification ushbu joyga muvaffaqiyatli bog'landi."
_UNBIND_OK = "🗑 Bog'lanish o'chirildi. Endi notifikatsiyalar yuborilmaydi."
_UNBIND_NONE = "ℹ️ Hech qanday aktiv bog'lanish yo'q."
_STATUS_NONE = "ℹ️ Hozircha hech qanday bog'lanish yo'q. /bind buyrug'idan foydalaning."


@router.message(CommandStart())
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Show the list of available commands."""
    await message.answer(HELP_TEXT)


@router.message(Command("bind"))
async def cmd_bind(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Bind notifications to the current chat/Topic (admins only)."""
    chat = message.chat
    if chat.type not in _GROUP_TYPES:
        await message.answer(_NOT_GROUP)
        return

    user = message.from_user
    if user is None or not await is_chat_admin(bot, chat.id, user.id):
        await message.answer(_NOT_ADMIN)
        return

    # Save the Topic id only for genuine forum Topic messages.
    thread_id = message.message_thread_id if message.is_topic_message else None
    await BindingRepository(session).set_active(chat_id=chat.id, message_thread_id=thread_id)
    logger.info("Binding set: chat_id={} thread_id={}", chat.id, thread_id)
    await message.answer(_BIND_OK)


@router.message(Command("unbind"))
async def cmd_unbind(message: Message, session: AsyncSession) -> None:
    """Remove the active binding."""
    removed = await BindingRepository(session).clear()
    await message.answer(_UNBIND_OK if removed else _UNBIND_NONE)


@router.message(Command("status"))
async def cmd_status(message: Message, session: AsyncSession) -> None:
    """Show the current binding details."""
    binding = await BindingRepository(session).get_active()
    if binding is None:
        await message.answer(_STATUS_NONE)
        return

    created_at = binding.created_at.strftime("%Y-%m-%d %H:%M:%S %Z").strip()
    await message.answer(
        "📋 <b>Joriy bog'lanish</b>\n\n"
        f"💬 <b>Chat ID:</b> <code>{binding.chat_id}</code>\n"
        f"🧵 <b>Topic ID:</b> <code>{binding.message_thread_id if binding.message_thread_id else '—'}</code>\n"
        f"🕒 <b>Created At:</b> {created_at}"
    )
