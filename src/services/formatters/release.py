from services.formatters.base import (
    MAX_TITLE_LEN,
    BaseFormatter,
    Payload,
    bold,
    esc,
    first_line,
    join_lines,
    link,
    project_name,
    project_url,
)

_ACTIONS: dict[str, str] = {
    "create": "🚀 <b>Release Published</b>",
    "update": "✏️ <b>Release Updated</b>",
    "delete": "🗑 <b>Release Deleted</b>",
}


class ReleaseFormatter(BaseFormatter):
    """Formats GitLab ``release`` events, keyed by ``action``."""

    object_kind = "release"

    def format(self, payload: Payload) -> str | None:
        action: str = payload.get("action") or ""
        header = _ACTIONS.get(action)
        if header is None:
            return None

        name = payload.get("name") or payload.get("tag") or ""
        tag = payload.get("tag", "")
        description = first_line(payload.get("description"), MAX_TITLE_LEN)

        base_url = project_url(payload)
        url = payload.get("url") or (f"{base_url}/-/releases/{tag}" if base_url and tag else None)

        return join_lines(
            header,
            "",
            f"📦 {link(project_name(payload), base_url)}",
            f"🎉 {bold('Release:')} {esc(name)}",
            f"🏷 {bold('Tag:')} {esc(tag)}",
            f"📝 {esc(description)}" if description else None,
            "" if url else None,
            f"🔗 {link('Open Release', url)}" if url else None,
        )
