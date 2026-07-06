from loguru import logger

from services.formatters.base import Payload
from services.formatters.registry import get_formatter


class GitLabDispatcher:
    """
    Turns a raw GitLab webhook payload into ready-to-send Telegram HTML.

    Selects a formatter by the payload's ``object_kind`` and delegates rendering.
    Returns ``None`` when the event is unsupported or intentionally skipped
    (e.g. an MR ``unapproved`` action or a non-MR comment).
    """

    def format_event(self, payload: Payload) -> str | None:
        """Render ``payload`` as Telegram HTML, or ``None`` when nothing to send."""
        object_kind = payload.get("object_kind")
        if not object_kind:
            logger.warning("GitLab payload has no 'object_kind'; ignoring")
            return None

        formatter = get_formatter(object_kind)
        if formatter is None:
            logger.info("No formatter registered for object_kind='{}'; ignoring", object_kind)
            return None

        message = formatter.format(payload)
        if message is None:
            logger.info("Formatter for object_kind='{}' skipped this event", object_kind)
        return message
