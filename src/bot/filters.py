from aiogram import Bot
from aiogram.enums import ChatMemberStatus

# Statuses that grant administrative rights in a chat.
_ADMIN_STATUSES = frozenset({ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR})


async def is_chat_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """
    Return whether ``user_id`` is an administrator (or the creator) of ``chat_id``.

    :param bot: the bot used to query chat membership.
    :param chat_id: Telegram chat ID.
    :param user_id: Telegram user ID to check.
    :return: ``True`` if the user is an admin/creator of the chat.
    """
    member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    return member.status in _ADMIN_STATUSES
