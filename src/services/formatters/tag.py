from services.formatters.base import (
    BaseFormatter,
    Payload,
    bold,
    branch_from_ref,
    esc,
    join_lines,
    link,
    project_name,
    project_url,
)

_ZERO_SHA = "0000000000000000000000000000000000000000"


class TagFormatter(BaseFormatter):
    """Formats GitLab ``tag_push`` events."""

    object_kind = "tag_push"

    def format(self, payload: Payload) -> str | None:
        tag = branch_from_ref(payload.get("ref"))
        before = payload.get("before")
        after = payload.get("after")

        if after == _ZERO_SHA:
            header = "🗑 <b>Tag Deleted</b>"
        elif before == _ZERO_SHA:
            header = "🏷 <b>Tag Created</b>"
        else:
            header = "🏷 <b>Tag Pushed</b>"

        base_url = project_url(payload)
        url = f"{base_url}/-/tags/{tag}" if base_url and tag and after != _ZERO_SHA else None

        return join_lines(
            header,
            "",
            f"📦 {link(project_name(payload), base_url)}",
            f"🏷 {bold('Tag:')} {esc(tag)}",
            f"👤 {bold('Author:')} {esc(payload.get('user_name') or '—')}",
            "" if url else None,
            f"🔗 {link('Open Tag', url)}" if url else None,
        )
