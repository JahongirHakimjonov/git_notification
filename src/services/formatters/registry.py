from services.formatters.base import BaseFormatter
from services.formatters.job import JobFormatter
from services.formatters.merge_request import MergeRequestFormatter
from services.formatters.note import NoteFormatter
from services.formatters.pipeline import PipelineFormatter
from services.formatters.push import PushFormatter
from services.formatters.release import ReleaseFormatter
from services.formatters.tag import TagFormatter

# object_kind -> formatter instance. Formatters are stateless, so single
# instances are reused. To support a new event type, add its formatter here.
_FORMATTERS: dict[str, BaseFormatter] = {
    formatter.object_kind: formatter
    for formatter in (
        PushFormatter(),
        TagFormatter(),
        MergeRequestFormatter(),
        PipelineFormatter(),
        JobFormatter(),
        NoteFormatter(),
        ReleaseFormatter(),
    )
}


def get_formatter(object_kind: str) -> BaseFormatter | None:
    """Return the formatter for a GitLab ``object_kind``, or ``None`` if unsupported."""
    return _FORMATTERS.get(object_kind)


def supported_kinds() -> tuple[str, ...]:
    """Return the tuple of supported GitLab ``object_kind`` values."""
    return tuple(_FORMATTERS)
