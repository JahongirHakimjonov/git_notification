import os
from functools import cache
from typing import Literal

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict
from yarl import URL

ENV_FILE_PATH = (
    {
        "local": ".env",
        "ci": ".env.ci",
        "test": ".env.test",
    }
).get(os.getenv("ENV", "local"), ".env")


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="allow",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return super().settings_customise_sources(
            settings_cls,
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )

    app_title: str = "FastAPI Template Project"
    app_name: str = "fastapidefault"
    env: Literal["local", "test", "ci", "dev", "prod"] = "prod"
    root_path: str = ""

    debug: bool = True

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = ""
    postgres_echo: bool = False

    sentry_dsn: str | None = None

    prometheus_metrics_key: str = "secret"

    # --- Telegram bot (aiogram, webhook mode) ---
    telegram_bot_token: str = ""
    # Public base URL where this service is reachable over HTTPS, e.g.
    # ``https://abc123.ngrok-free.app``. When empty the webhook is NOT
    # registered on startup (so ``docker compose up`` never crashes without it).
    telegram_webhook_url: str = ""
    telegram_webhook_path: str = "/webhook/telegram"
    # Value echoed by Telegram in the ``X-Telegram-Bot-Api-Secret-Token`` header;
    # protects the webhook endpoint from spoofed calls.
    telegram_webhook_secret: str = ""
    telegram_request_timeout: float = 20.0

    # --- GitLab webhook ---
    # Compared against the ``X-Gitlab-Token`` header; mismatch -> HTTP 403.
    gitlab_webhook_secret: str = ""

    @property
    def postgres_url(self) -> str:
        return str(
            URL.build(
                scheme="postgresql+asyncpg",
                host=self.postgres_host,
                port=self.postgres_port,
                user=self.postgres_user,
                password=self.postgres_password,
                path=f"/{self.postgres_db}",
            )
        )

    @property
    def telegram_webhook_full_url(self) -> str:
        """Full public URL Telegram will POST updates to."""
        return self.telegram_webhook_url.rstrip("/") + self.telegram_webhook_path

    @property
    def telegram_enabled(self) -> bool:
        """Whether the bot can run (a token is configured)."""
        return bool(self.telegram_bot_token)


@cache
def get_settings() -> Settings:
    return Settings()
