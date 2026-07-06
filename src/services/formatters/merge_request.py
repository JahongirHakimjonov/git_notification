from services.formatters.base import (
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

# action -> (header emoji + title, label describing the actor)
_ACTIONS: dict[str, tuple[str, str]] = {
    "open": ("🔀 <b>Merge Request Opened</b>", "Author:"),
    "update": ("✏️ <b>Merge Request Updated</b>", "Updated by:"),
    "approved": ("✅ <b>Merge Request Approved</b>", "Approved by:"),
    "merge": ("🎉 <b>Merge Completed</b>", "Merged by:"),
    "close": ("❌ <b>Merge Request Closed</b>", "Closed by:"),
    "reopen": ("🔄 <b>Merge Request Reopened</b>", "Reopened by:"),
}


class MergeRequestFormatter(BaseFormatter):
    """Formats GitLab ``merge_request`` events, keyed by ``object_attributes.action``."""

    object_kind = "merge_request"

    def format(self, payload: Payload) -> str | None:
        attrs = payload.get("object_attributes") or {}
        action: str = attrs.get("action") or ""
        header_label = _ACTIONS.get(action)
        if header_label is None:
            # Unsupported action (e.g. "unapproved") — silently ignore.
            return None
        header, actor_label = header_label

        source = attrs.get("source_branch", "")
        target = attrs.get("target_branch", "")
        iid = attrs.get("iid")
        title = first_line(attrs.get("title"), MAX_TITLE_LEN)
        url = attrs.get("url")

        mr_label = f"Open Merge Request !{iid}" if iid else "Open Merge Request"

        return join_lines(
            header,
            "",
            f"📦 {link(project_name(payload), project_url(payload))}",
            "",
            f"🌿 {esc(source)} ➡️ {esc(target)}",
            "",
            f"👤 {bold(actor_label)} {esc(actor_name(payload))}",
            f"📄 {esc(title)}" if title else None,
            "" if url else None,
            f"🔗 {link(mr_label, url)}" if url else None,
        )
