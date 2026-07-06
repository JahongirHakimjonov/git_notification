from abc import ABC, abstractmethod
from html import escape
from typing import Any, ClassVar

# --- Formatting limits (avoid magic numbers) ---
MAX_COMMITS_SHOWN = 10
MAX_COMMIT_MESSAGE_LEN = 100
MAX_TITLE_LEN = 200
MAX_NOTE_LEN = 300

Payload = dict[str, Any]


def esc(value: Any) -> str:
    """HTML-escape an arbitrary value for safe inclusion in a Telegram message."""
    return escape(str(value), quote=False)


def bold(value: Any) -> str:
    return f"<b>{esc(value)}</b>"


def code(value: Any) -> str:
    return f"<code>{esc(value)}</code>"


def link(text: str, url: str | None) -> str:
    """Render an HTML link, or just the escaped text when no URL is available."""
    if not url:
        return esc(text)
    return f'<a href="{esc(url)}">{esc(text)}</a>'


def first_line(text: str | None, limit: int) -> str:
    """Return the first line of ``text``, trimmed to ``limit`` characters."""
    if not text:
        return ""
    line = text.strip().splitlines()[0] if text.strip() else ""
    if len(line) > limit:
        return line[: limit - 1].rstrip() + "…"
    return line


def branch_from_ref(ref: str | None) -> str:
    """Extract a branch or tag name from a Git ref (``refs/heads/main`` -> ``main``)."""
    if not ref:
        return ""
    for prefix in ("refs/heads/", "refs/tags/"):
        if ref.startswith(prefix):
            return ref[len(prefix) :]
    return ref


def project_name(payload: Payload) -> str:
    """Best-effort project name across the different GitLab hook payload shapes."""
    project = payload.get("project") or {}
    return project.get("name") or project.get("path_with_namespace") or payload.get("project_name") or "—"


def project_url(payload: Payload) -> str | None:
    project = payload.get("project") or {}
    repository = payload.get("repository") or {}
    return project.get("web_url") or repository.get("homepage") or None


def actor_name(payload: Payload) -> str:
    """Name of the user who triggered the event (payloads use ``user`` or ``user_name``)."""
    user = payload.get("user")
    if isinstance(user, dict):
        return user.get("name") or user.get("username") or "—"
    return payload.get("user_name") or "—"


def join_lines(*lines: str | None) -> str:
    """
    Join message lines with newlines.

    ``None`` entries are dropped (use them for conditionally-omitted lines);
    empty strings are kept as intentional blank separators.
    """
    return "\n".join(line for line in lines if line is not None)


class BaseFormatter(ABC):
    """
    Base class for GitLab event formatters.

    Subclasses declare which ``object_kind`` they handle and implement
    :meth:`format`, returning ready-to-send Telegram HTML, or ``None`` when the
    particular event should be silently ignored (e.g. an unsupported sub-action).
    """

    object_kind: ClassVar[str]

    @abstractmethod
    def format(self, payload: Payload) -> str | None:
        """Render ``payload`` as Telegram HTML, or ``None`` to skip it."""
        raise NotImplementedError
