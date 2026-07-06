# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A **GitLab-webhook → Telegram notification service** (FastAPI + async SQLAlchemy 2.0 +
Alembic + PostgreSQL), managed with `uv` and driven by a `Taskfile`. One FastAPI app hosts
both a **GitLab webhook** endpoint and an **aiogram 3.x Telegram bot in webhook mode**
(no polling). GitLab events (Push, Merge Request, Pipeline, Job, Tag, Release, Note) are
formatted as HTML and delivered to the single bound Telegram chat/Topic. Built on the
`fastapi-template` scaffold (whose `Dummy` example resource has been removed). README and bot
user-facing strings are in **Uzbek**; notification field labels are in English. Some template
monitoring docstrings remain in Russian.

## Commands

All tasks run through `task` (Taskfile.yml), which wraps `uv run`. If `task` isn't installed,
prefix with `uvx --from go-task-bin task <target>`, or run the underlying `uv run ...` directly.

- `task init` — one-time setup: `uv sync`, start Postgres, apply migrations.
- `task run` — start Postgres + migrate + `fastapi dev src/dev.py` (dev server on :8000).
- `task lint` — `ruff check` + `ruff format --check` over `src tests`.
- `task format` (alias `fmt`) — `ruff format` + `ruff check --fix`.
- `task typecheck` — `mypy src` (strict).
- `task deptry` — unused/missing-dependency check.
- `task test` — start `postgres-test`, then `ENV=test uv run pytest -vv`.
- `task testcov` — tests + coverage report/xml.
- `task all` (default) — the full CI check set: format → deptry → typecheck → testcov.
- `task pre-commit` — run the pre-commit hooks (they call the tasks above).

**Running a single test** (webhook/repository tests require Postgres: `docker compose up -d
postgres-test`; formatter/notifier tests are DB-free):
```bash
ENV=test uv run pytest tests/test_formatters.py::test_push_formatter_renders_key_fields
ENV=test uv run pytest -k "keyword"                        # by keyword
```
`ENV=test` is required — it selects `.env.test` and the test Postgres (host port 25439).

**Migrations** (Alembic; config at `src/alembic.ini`, versions in `src/db/migrations/versions/`):
Alembic resolves `alembic.ini` and its models relative to the current directory, and the config
lives only under `src/`, so run manual alembic commands from there:
```bash
cd src && ENV=local uv run alembic upgrade head                          # apply
cd src && ENV=local uv run alembic revision --autogenerate -m "message"  # create
```
Models are auto-discovered via `load_all_models()`, so no manual registration is needed. The
`task init`/`task upgrade-db` targets and the container entrypoint also run migrations as part of
their own flows.

## Environment

Config is `pydantic-settings` (`src/core/settings.py`). The `ENV` variable
(`local|test|ci|dev|prod`, default `prod`) selects the dotenv file at import time:
`local→.env`, `ci→.env.ci`, `test→.env.test`. **No `.env` is committed** — copy `.env.example`
to `.env` first. Key vars: `POSTGRES_*`, `DEBUG`, `APP_NAME`, `SENTRY_DSN`,
`PROMETHEUS_METRICS_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_URL`,
`TELEGRAM_WEBHOOK_SECRET`, `GITLAB_WEBHOOK_SECRET`. Note: dotenv values **override** process
env vars (custom `settings_customise_sources`) — so **`POSTGRES_HOST` is deliberately kept out
of `.env`** and injected by docker-compose's `environment:` (as `postgres`); the field default
`localhost` covers local runs. The Telegram webhook is only registered when
`TELEGRAM_WEBHOOK_URL` is set (needs a public HTTPS URL — use a tunnel locally); otherwise the
app still boots.

## Architecture

`src` is the package root (installed via uv `package = true`), so imports are top-level:
`from core.settings import ...`, `from db.crud.binding import ...` — **never** `from src....`.

**Entry points / app factory** — `create_app()` in `src/app.py` builds the FastAPI app
(loads settings → configures loguru → optional Sentry → middleware → routers → exception
handlers). Routers are mounted at the **root** (no `/api` prefix) because GitLab/Telegram
need fixed paths. `src/dev.py` (`fastapi dev`) and `src/main.py` (uvicorn `--factory`) are the
launchers; containers run `uvicorn app:create_app --factory`. `docs`/`openapi` only when `DEBUG`.

**Request flow / layers:**
```
api/webhooks/gitlab.py     POST /webhook/gitlab — validate X-Gitlab-Token (403), then
                           format via GitLabDispatcher and deliver in a BackgroundTask
                           (return 200 immediately — never 5xx to GitLab)
api/webhooks/telegram.py   POST /webhook/telegram — validate secret header, feed_update()
api/health.py              GET /health -> {"status":"ok"}
services/gitlab/dispatcher.py   object_kind -> formatter
services/formatters/*      one BaseFormatter subclass per event + registry.py; format()
                           returns HTML or None (None = ignore); all user content HTML-escaped
services/telegram/notifier.py   fetch active Binding, send_message (retry on transient errors)
bot/ (aiogram)             instance.get_bot() [@cache], setup.get_dispatcher() [@cache],
                           handlers/commands.py (/bind /unbind /status /help),
                           middlewares.DatabaseMiddleware (injects `session`), filters.is_chat_admin
db/models/binding.py       Binding: chat_id (BigInteger), message_thread_id (nullable), timestamps
db/crud/binding.py         BindingRepository — set_active() deletes-then-inserts (one active binding)
```
New models under `db/models/` are auto-imported by `load_all_models()` (Alembic + tests) — no
manual wiring.

**Infra as `@cache` singletons** — `get_settings`, `get_db_engine`, `get_session_factory`
(`core/database.py`), `get_http_transport` (`core/requests.py`), `get_metrics`
(`core/prometheus.py`), `get_bot` (`bot/instance.py`), `get_dispatcher` (`bot/setup.py`). The
`lifespan` (`core/lifespan.py`) eagerly creates the engine + HTTP transport, and when
`telegram_enabled` registers the Telegram webhook + commands on startup / deletes the webhook
and closes the bot session on shutdown.

**DB session** — `get_db_session` (`db/dependencies.py`) yields a session and
**commits on success / rolls back on exception**. Shared `MetaData` with `ix/uq/ck/fk/pk`
naming conventions lives in `db/meta.py` (attached to `Base` in `db/base.py`).

**Monitoring** — `core/monitoring.py` serves `/healthcheck`, `/status`, `/version`, and
`/metrics` (Prometheus; gated by a `key` header vs `PROMETHEUS_METRICS_KEY`, else 403); plus a
plain `GET /health` (`api/health.py`). `MetricsMiddleware` (`core/prometheus.py`) records
request count/latency for `/api*` **and `/webhook*`**. `RequestLoggingMiddleware`
(`core/middleware.py`) logs every request. `register_exception_handlers` (`core/exceptions.py`)
handles `APIException`, `RequestValidationError`, `SQLAlchemyError`, aiogram `TelegramAPIError`,
and any unhandled `Exception` — all as the `{detail, code, variables}` envelope, with stack
traces logged for server-side failures.

**Tests** (`tests/conftest.py`) — anyio/asyncio. Each test runs in a connection-level
transaction that is **rolled back afterward** (SAVEPOINT isolation); `fastapi_app` overrides
`get_db_session` to inject the test session; `client` uses httpx `ASGITransport`.

## Conventions & gotchas

- Ruff: line length **120**, target **py312**, migrations excluded. mypy is **strict**. Ruff
  is the only formatter (it subsumes `black`/`isort`).
- Docker/Postgres is required for `task test` and `task run`.
- Celery worker/beat/flower scripts exist under `deployments/` but Celery is **not** a
  dependency and its compose services are commented out — it's opt-in scaffolding, not wired up.
