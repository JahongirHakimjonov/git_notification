from services.formatters.base import (
    BaseFormatter,
    Payload,
    actor_name,
    bold,
    esc,
    join_lines,
    link,
    project_name,
    project_url,
)

# Pipeline statuses we notify on -> header. Other statuses (pending, created,
# manual, ...) are ignored to avoid noise.
_STATUSES: dict[str, str] = {
    "running": "🏃 <b>Pipeline Running</b>",
    "success": "✅ <b>Pipeline Success</b>",
    "failed": "❌ <b>Pipeline Failed</b>",
    "canceled": "🚫 <b>Pipeline Canceled</b>",
    "skipped": "⏭ <b>Pipeline Skipped</b>",
}


class PipelineFormatter(BaseFormatter):
    """Formats GitLab ``pipeline`` events, keyed by ``object_attributes.status``."""

    object_kind = "pipeline"

    def format(self, payload: Payload) -> str | None:
        attrs = payload.get("object_attributes") or {}
        status: str = attrs.get("status") or ""
        header = _STATUSES.get(status)
        if header is None:
            return None

        pipeline_id = attrs.get("id")
        ref = attrs.get("ref", "")
        duration = attrs.get("duration")

        base_url = project_url(payload)
        url = attrs.get("url") or (f"{base_url}/-/pipelines/{pipeline_id}" if base_url and pipeline_id else None)

        duration_line = f"⏱ {bold('Duration:')} {esc(duration)}s" if duration is not None else None

        return join_lines(
            header,
            "",
            f"📦 {link(project_name(payload), base_url)}",
            f"🌿 {bold('Branch:')} {esc(ref)}",
            f"👤 {bold('Triggered by:')} {esc(actor_name(payload))}",
            duration_line,
            f"🆔 {bold('Pipeline:')} #{esc(pipeline_id)}" if pipeline_id else None,
            "" if url else None,
            f"🔗 {link('Open Pipeline', url)}" if url else None,
        )
