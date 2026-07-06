from services.gitlab.dispatcher import GitLabDispatcher
from tests import payloads

dispatcher = GitLabDispatcher()


def test_push_formatter_renders_key_fields() -> None:
    message = dispatcher.format_event(payloads.PUSH)
    assert message is not None
    assert "PUSH" in message
    assert "backend-api" in message
    assert "main" in message
    assert "Ali" in message
    assert "Fix login" in message  # only the first line of the commit message
    assert "details" not in message
    assert '<a href="https://gitlab.example/c/2">Open Commit</a>' in message


def test_new_branch_has_distinct_header() -> None:
    message = dispatcher.format_event(payloads.NEW_BRANCH)
    assert message is not None
    assert "NEW BRANCH" in message


def test_tag_formatter() -> None:
    message = dispatcher.format_event(payloads.TAG_PUSH)
    assert message is not None
    assert "Tag Created" in message
    assert "v1.2.0" in message


def test_merge_request_merged() -> None:
    message = dispatcher.format_event(payloads.MERGE_REQUEST_MERGED)
    assert message is not None
    assert "Merge Completed" in message
    assert "feature/auth" in message
    assert "main" in message
    assert "Merged by:" in message
    assert "Open Merge Request !7" in message


def test_merge_request_unapproved_is_ignored() -> None:
    assert dispatcher.format_event(payloads.MERGE_REQUEST_UNAPPROVED) is None


def test_pipeline_success() -> None:
    message = dispatcher.format_event(payloads.PIPELINE_SUCCESS)
    assert message is not None
    assert "Pipeline Success" in message
    assert "42s" in message
    assert "/-/pipelines/55" in message


def test_pipeline_pending_is_ignored() -> None:
    assert dispatcher.format_event(payloads.PIPELINE_PENDING) is None


def test_job_failed() -> None:
    message = dispatcher.format_event(payloads.JOB_FAILED)
    assert message is not None
    assert "Job Failed" in message
    assert "pytest" in message
    assert "script_failure" in message
    assert "/-/jobs/99" in message


def test_note_on_merge_request() -> None:
    message = dispatcher.format_event(payloads.NOTE_MR)
    assert message is not None
    assert "MR Comment" in message
    assert "Looks good to me" in message
    assert "MR !7" in message


def test_note_on_issue_is_ignored() -> None:
    assert dispatcher.format_event(payloads.NOTE_ISSUE) is None


def test_release_created() -> None:
    message = dispatcher.format_event(payloads.RELEASE_CREATED)
    assert message is not None
    assert "Release Published" in message
    assert "v1.2.0" in message


def test_unknown_object_kind_returns_none() -> None:
    assert dispatcher.format_event({"object_kind": "wiki_page"}) is None
    assert dispatcher.format_event({}) is None


def test_user_content_is_html_escaped() -> None:
    message = dispatcher.format_event(payloads.PUSH_WITH_HTML)
    assert message is not None
    # Raw user input must be escaped so it can't inject Telegram HTML markup.
    assert "<script>" not in message
    assert "&lt;script&gt;" in message
    assert "&lt;b&gt;evil&lt;/b&gt; &amp; co" in message
