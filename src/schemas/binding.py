from datetime import datetime

from pydantic import Field

from .base import BaseSchema


class Binding(BaseSchema):
    """DTO for a notification :class:`db.models.binding.Binding`."""

    id: int = Field(title="ID", examples=[1])
    chat_id: int = Field(title="Telegram chat ID", examples=[-1001234567890])
    message_thread_id: int | None = Field(
        default=None,
        title="Forum Topic ID",
        examples=[42],
    )
    created_at: datetime = Field(title="Created at")
    updated_at: datetime = Field(title="Updated at")
