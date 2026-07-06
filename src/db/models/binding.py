from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Binding(Base):
    """
    Links notifications to a single Telegram destination.

    A binding stores where GitLab notifications should be delivered: a chat and,
    optionally, a forum ``message_thread_id`` (Topic). Only one binding is active
    at a time — creating a new one via ``/bind`` replaces the previous one (see
    :class:`db.crud.binding.BindingRepository`).
    """

    __tablename__ = "binding"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # BigInteger: Telegram supergroup/channel chat IDs exceed the int32 range.
    chat_id: Mapped[int] = mapped_column(BigInteger)
    # NULL when bound to a regular chat (not a forum Topic).
    message_thread_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
