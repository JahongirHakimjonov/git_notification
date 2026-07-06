from services.formatters.base import (
    MAX_NOTE_LEN,
    MAX_TITLE_LEN,
    BaseFormatter,
    Payload,
    actor_name,
    bold,
    esc,
    first_line,
    join_lines,
    link,
    project_name,
    project_url,
)


class NoteFormatter(BaseFormatter):
    """Formats GitLab ``note`` events — Merge Request comments only."""

    object_kind = "note"

    def format(self, payload: Payload) -> str | None:
        attrs = payload.get("object_attributes") or {}
        # Only Merge Request comments are supported (per spec).
        if attrs.get("noteable_type") != "MergeRequest":
            return None

        mr = payload.get("merge_request") or {}
        iid = mr.get("iid")
        title = first_line(mr.get("title"), MAX_TITLE_LEN)
        note = first_line(attrs.get("note"), MAX_NOTE_LEN)
        url = attrs.get("url")

        if iid:
            mr_line: str | None = f"🔀 {bold(f'MR !{iid}:')} {esc(title)}"
        elif title:
            mr_line = f"🔀 {esc(title)}"
        else:
            mr_line = None

        return join_lines(
            "💬 <b>New MR Comment</b>",
            "",
            f"📦 {link(project_name(payload), project_url(payload))}",
            mr_line,
            f"👤 {bold('By:')} {esc(actor_name(payload))}",
            f"🗨 {esc(note)}" if note else None,
            "" if url else None,
            f"🔗 {link('Open Comment', url)}" if url else None,
        )
