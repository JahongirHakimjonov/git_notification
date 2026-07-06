from fastapi.routing import APIRouter

from api.health import router as health_router
from api.webhooks.gitlab import router as gitlab_router
from api.webhooks.telegram import router as telegram_router

# Root-level router aggregating public endpoints (webhooks + health).
# Mounted without the ``/api`` prefix in ``create_app`` because GitLab and
# Telegram require fixed paths (``/webhook/gitlab``, ``/webhook/telegram``).
api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(gitlab_router)
api_router.include_router(telegram_router)
