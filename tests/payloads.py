"""Representative GitLab webhook payloads for tests (trimmed to fields we use)."""

from typing import Any

_ZERO = "0" * 40

PUSH: dict[str, Any] = {
    "object_kind": "push",
    "ref": "refs/heads/main",
    "before": "a" * 40,
    "after": "b" * 40,
    "user_name": "Ali",
    "total_commits_count": 2,
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "commits": [
        {"message": "Fix login\n\ndetails", "url": "https://gitlab.example/c/1"},
        {"message": "Update auth", "url": "https://gitlab.example/c/2"},
    ],
}

NEW_BRANCH: dict[str, Any] = {**PUSH, "before": _ZERO}

TAG_PUSH: dict[str, Any] = {
    "object_kind": "tag_push",
    "ref": "refs/tags/v1.2.0",
    "before": _ZERO,
    "after": "c" * 40,
    "user_name": "Ali",
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "commits": [],
}

MERGE_REQUEST_MERGED: dict[str, Any] = {
    "object_kind": "merge_request",
    "user": {"name": "Ali", "username": "ali"},
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "object_attributes": {
        "action": "merge",
        "iid": 7,
        "title": "Add authentication",
        "source_branch": "feature/auth",
        "target_branch": "main",
        "url": "https://gitlab.example/backend-api/-/merge_requests/7",
    },
}

MERGE_REQUEST_UNAPPROVED: dict[str, Any] = {
    "object_kind": "merge_request",
    "user": {"name": "Ali"},
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "object_attributes": {"action": "unapproved", "iid": 7, "title": "x", "url": "u"},
}

PIPELINE_SUCCESS: dict[str, Any] = {
    "object_kind": "pipeline",
    "user": {"name": "Ali"},
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "object_attributes": {"id": 55, "ref": "main", "status": "success", "duration": 42},
    "commit": {"id": "deadbeef", "message": "Fix login", "url": "https://gitlab.example/c/1"},
}

PIPELINE_PENDING: dict[str, Any] = {
    "object_kind": "pipeline",
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "object_attributes": {"id": 56, "ref": "main", "status": "pending"},
}

JOB_FAILED: dict[str, Any] = {
    "object_kind": "build",
    "ref": "main",
    "build_id": 99,
    "build_name": "pytest",
    "build_stage": "test",
    "build_status": "failed",
    "build_duration": 12.34,
    "build_failure_reason": "script_failure",
    "project_name": "backend-api",
    "user": {"name": "Ali"},
    "repository": {"name": "backend-api", "homepage": "https://gitlab.example/backend-api"},
}

NOTE_MR: dict[str, Any] = {
    "object_kind": "note",
    "user": {"name": "Ali"},
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "object_attributes": {
        "noteable_type": "MergeRequest",
        "note": "Looks good to me",
        "url": "https://gitlab.example/backend-api/-/merge_requests/7#note_1",
    },
    "merge_request": {"iid": 7, "title": "Add authentication"},
}

NOTE_ISSUE: dict[str, Any] = {
    "object_kind": "note",
    "user": {"name": "Ali"},
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "object_attributes": {"noteable_type": "Issue", "note": "hi", "url": "u"},
}

RELEASE_CREATED: dict[str, Any] = {
    "object_kind": "release",
    "action": "create",
    "name": "v1.2.0",
    "tag": "v1.2.0",
    "description": "First stable release",
    "url": "https://gitlab.example/backend-api/-/releases/v1.2.0",
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
}

# XSS/HTML-escaping check: user content containing angle brackets.
PUSH_WITH_HTML: dict[str, Any] = {
    "object_kind": "push",
    "ref": "refs/heads/main",
    "before": "a" * 40,
    "after": "b" * 40,
    "user_name": "<script>alert(1)</script>",
    "total_commits_count": 1,
    "project": {"name": "backend-api", "web_url": "https://gitlab.example/backend-api"},
    "commits": [{"message": "<b>evil</b> & co", "url": "https://gitlab.example/c/1"}],
}
