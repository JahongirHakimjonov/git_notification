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

# GitLab Job hooks use object_kind "build". We notify on terminal outcomes only.
_STATUSES: dict[str, str] = {
    "success": "✅ <b>Job Success</b>",
    "failed": "❌ <b>Job Failed</b>",
}


class JobFormatter(BaseFormatter):
    """Formats GitLab ``build`` (Job) events, keyed by ``build_status``."""

    object_kind = "build"

    def format(self, payload: Payload) -> str | None:
        status: str = payload.get("build_status") or ""
        header = _STATUSES.get(status)
        if header is None:
            return None

        build_id = payload.get("build_id")
        name = payload.get("build_name", "")
        stage = payload.get("build_stage", "")
        ref = payload.get("ref", "")
        duration = payload.get("build_duration")
        failure_reason = payload.get("build_failure_reason")

        base_url = project_url(payload)
        url = f"{base_url}/-/jobs/{build_id}" if base_url and build_id else None

        lines = [
            header,
            "",
            f"📦 {link(project_name(payload), base_url)}",
            f"🌿 {bold('Branch:')} {esc(ref)}",
            f"🔧 {bold('Job:')} {esc(name)} ({esc(stage)})",
            f"👤 {bold('Author:')} {esc(actor_name(payload))}",
        ]
        if duration is not None:
            lines.append(f"⏱ {bold('Duration:')} {esc(round(float(duration), 1))}s")
        if status == "failed" and failure_reason:
            lines.append(f"⚠️ {bold('Reason:')} {esc(failure_reason)}")
        if url:
            lines += ["", f"🔗 {link('Open Job', url)}"]
        return join_lines(*lines)
