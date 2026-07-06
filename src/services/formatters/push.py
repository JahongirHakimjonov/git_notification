from services.formatters.base import (
    MAX_COMMIT_MESSAGE_LEN,
    MAX_COMMITS_SHOWN,
    BaseFormatter,
    Payload,
    bold,
    branch_from_ref,
    esc,
    first_line,
    join_lines,
    link,
    project_name,
    project_url,
)

# A ref pointing at the all-zero SHA means the branch was created or deleted.
_ZERO_SHA = "0000000000000000000000000000000000000000"


class PushFormatter(BaseFormatter):
    """Formats GitLab ``push`` events (commits pushed to a branch)."""

    object_kind = "push"

    def format(self, payload: Payload) -> str | None:
        branch = branch_from_ref(payload.get("ref"))
        before = payload.get("before")
        after = payload.get("after")
        commits = payload.get("commits") or []
        total = payload.get("total_commits_count", len(commits))

        if after == _ZERO_SHA:
            return join_lines(
                f"🗑 {bold('BRANCH DELETED')}",
                "",
                f"📦 {bold('Project:')} {link(project_name(payload), project_url(payload))}",
                f"🌿 {bold('Branch:')} {esc(branch)}",
                f"👤 {bold('Author:')} {esc(payload.get('user_name') or '—')}",
            )

        header = "🌱 <b>NEW BRANCH</b>" if before == _ZERO_SHA else "🚀 <b>PUSH</b>"

        commit_lines = []
        for commit in commits[:MAX_COMMITS_SHOWN]:
            message = first_line(commit.get("message"), MAX_COMMIT_MESSAGE_LEN)
            commit_lines.append(f"• {esc(message)}")
        if total > MAX_COMMITS_SHOWN:
            commit_lines.append(f"… {esc(total - MAX_COMMITS_SHOWN)} ta ko'proq")

        last_commit_url = commits[-1].get("url") if commits else None

        return join_lines(
            header,
            "",
            f"📦 {bold('Project:')} {link(project_name(payload), project_url(payload))}",
            f"🌿 {bold('Branch:')} {esc(branch)}",
            f"👤 {bold('Author:')} {esc(payload.get('user_name') or '—')}",
            "",
            f"💬 {bold(f'Commits ({total}):')}",
            *commit_lines,
            "" if last_commit_url else None,
            f"🔗 {link('Open Commit', last_commit_url)}" if last_commit_url else None,
        )
