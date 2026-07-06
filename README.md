# GitLab → Telegram Notifier

GitLab webhook eventlarini (Push, Merge Request, Pipeline, Job, Tag, Release,
Note) Telegram guruhiga yoki forum **Topic**'iga chiroyli HTML formatida yuboradigan
production-ready xizmat.

Bitta **FastAPI** ilovasi ichida ikkita narsa birlashgan:

- **Telegram bot** (aiogram 3.x, **webhook** rejimida — polling ishlatilmaydi),
- **GitLab webhook** qabul qiluvchi endpoint.

GitLab → FastAPI → PostgreSQL → Telegram.

---

## Texnologiyalar

- Python 3.12+
- FastAPI, Uvicorn
- aiogram 3.x (Telegram Bot API, webhook)
- SQLAlchemy 2.x (async) + asyncpg, PostgreSQL
- Alembic (migratsiyalar)
- Pydantic v2, pydantic-settings
- Docker, Docker Compose (multi-stage, kichik image)
- Ruff (lint + format, `black` va `isort` o'rnini bosadi), mypy (strict)
- pytest
- loguru (logging), Sentry va Prometheus (ixtiyoriy monitoring)

---

## Arxitektura

Vertikal qatlamlar (`src/` ichida):

```
api/
  health.py              GET /health
  webhooks/gitlab.py     POST /webhook/gitlab   (X-Gitlab-Token tekshiradi)
  webhooks/telegram.py   POST /webhook/telegram (X-Telegram secret tekshiradi)
bot/
  instance.py            Bot singletoni (HTML parse mode)
  setup.py               Dispatcher, webhook o'rnatish/o'chirish, komandalar
  middlewares.py         Har handlerga DB session beradi
  filters.py             Admin tekshiruvi
  handlers/commands.py   /bind /unbind /status /help
db/
  models/binding.py      Binding modeli
  crud/binding.py        BindingRepository (bitta aktiv binding)
schemas/binding.py       Pydantic DTO
services/
  formatters/            Har event uchun alohida formatter + registry
  gitlab/dispatcher.py   object_kind -> formatter
  telegram/notifier.py   aktiv binding'ga xabar yuboradi (retry bilan)
```

Ma'lumot oqimi:

```
GitLab  →  POST /webhook/gitlab  →  X-Gitlab-Token tekshirish (xato bo'lsa 403)
        →  GitLabDispatcher (object_kind bo'yicha formatter)
        →  BackgroundTask: TelegramNotifier  →  aktiv Binding (chat + Topic)
        →  Telegram guruh / Topic
```

Telegram xatolari **hech qachon** GitLab'ga 5xx bo'lib qaytmaydi — format qilish va
yuborish fon vazifasida bajariladi, endpoint darhol `200` qaytaradi.

---

## O'rnatish

### 1-usul: Docker Compose (tavsiya etiladi)

Talab: Docker va Docker Compose.

```bash
cp .env.example .env      # keyin .env ni tahrirlang (pastga qarang)
docker compose up --build
```

Bu quyidagilarni avtomatik bajaradi:

1. PostgreSQL ko'tariladi va tayyor bo'lguncha kutiladi (healthcheck),
2. Alembic migratsiyalari qo'llaniladi (`binding` jadvali yaratiladi),
3. FastAPI ilovasi ishga tushadi (`:8001` portda, `${PORT}` bilan o'zgartiriladi),
4. `TELEGRAM_WEBHOOK_URL` berilgan bo'lsa, Telegram webhook avtomatik o'rnatiladi.

Ishlayotganini tekshirish:

```bash
curl http://localhost:8001/health      # {"status":"ok"}
```

Swagger UI (faqat `DEBUG=true` bo'lganda): http://localhost:8001/docs

### 2-usul: Lokal (uv + Task)

Talab: [uv](https://docs.astral.sh/uv/), Docker, [Task](https://taskfile.dev).

```bash
task init      # uv sync + postgres + migratsiyalar
task run       # postgres + migratsiya + fastapi dev (:8000)
```

`task` o'rnatilmagan bo'lsa: `uvx --from go-task-bin task <target>`.

---

## Muhit sozlamalari (`.env`)

`.env.example` dan nusxa oling. Asosiy o'zgaruvchilar:

| O'zgaruvchi | Tavsif |
|---|---|
| `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Ma'lumotlar bazasi |
| `TELEGRAM_BOT_TOKEN` | @BotFather bergan token (majburiy) |
| `TELEGRAM_WEBHOOK_URL` | Xizmatning ochiq HTTPS bazaviy URL'i (masalan `https://xxx.ngrok-free.app`). Bo'sh bo'lsa webhook o'rnatilmaydi. |
| `TELEGRAM_WEBHOOK_SECRET` | Telegram `X-Telegram-Bot-Api-Secret-Token` orqali qaytaradigan maxfiy so'z |
| `GITLAB_WEBHOOK_SECRET` | GitLab webhook "Secret token"i bilan mos bo'lishi shart |
| `PROMETHEUS_METRICS_KEY`, `SENTRY_DSN`, `DEBUG` | Monitoring / rejim |

> ⚠️ **`POSTGRES_HOST` `.env` faylida bo'lmasligi kerak.** Bu loyihada dotenv qiymatlari
> process env'dan ustun turadi, shuning uchun Docker Compose `app` xizmatiga
> `POSTGRES_HOST=postgres` ni `environment:` orqali beradi. Lokal ishda esa u
> `localhost` ga standart bo'ladi.

---

## Alembic migratsiya

Docker'da migratsiyalar avtomatik qo'llaniladi. Qo'lda ishlatish (`src/` ichidan):

```bash
cd src && ENV=local uv run alembic upgrade head                          # qo'llash
cd src && ENV=local uv run alembic revision --autogenerate -m "xabar"    # yaratish
```

Modellar `load_all_models()` orqali avtomatik topiladi — qo'lda ro'yxatga olish shart emas.

---

## Telegram bot yaratish (@BotFather)

1. Telegram'da [@BotFather](https://t.me/BotFather) ga `/newbot` yuboring.
2. Bot nomi va username'ini bering, tokenni oling → `TELEGRAM_BOT_TOKEN` ga qo'ying.
3. **Muhim:** bot guruh xabarlarini ko'rishi uchun @BotFather → `/setprivacy` →
   botni tanlang → **Disable** (Privacy Mode **o'chirilgan** bo'lishi kerak),
   aks holda bot `/bind` kabi komandalarni ko'rmaydi.

## Telegram Webhook sozlash

Telegram webhook **ochiq HTTPS URL** talab qiladi. Lokal ishlab chiqishda tunnel ishlating:

```bash
# ngrok misoli
ngrok http 8001
# yoki cloudflared
cloudflared tunnel --url http://localhost:8001
```

Chiqqan HTTPS URL'ni `.env` ga qo'ying:

```
TELEGRAM_WEBHOOK_URL=https://<sizning-tunnel>.ngrok-free.app
```

Ilova **startup** vaqtida webhookni avtomatik o'rnatadi (`/webhook/telegram`) va
**shutdown** vaqtida o'chiradi. Alohida buyruq kerak emas.

## Botni guruhga qo'shish

1. Botni Telegram guruhingizga qo'shing.
2. Botni guruh **administratori** qiling (kamida xabar yuborish huquqi bilan).
3. Guruhda `/bind` yuboring (faqat admin ishlata oladi):

   > ✅ Notification ushbu joyga muvaffaqiyatli bog'landi.

## Topic (Forum) bilan ishlatish

1. Guruh sozlamalarida **Topics** (forum rejimi) yoqilgan bo'lsin.
2. Kerakli Topic ichiga kiring va o'sha yerda `/bind` yuboring.
3. Bot `chat_id` bilan birga `message_thread_id` ni ham saqlaydi — barcha
   notifikatsiyalar aynan o'sha Topic ichiga tushadi.

Oddiy chatda `/bind` qilinsa, `message_thread_id` `NULL` bo'ladi va xabarlar
guruhning umumiy oqimiga yuboriladi.

---

## Bot komandalar

| Komanda | Tavsif |
|---|---|
| `/bind` | Ushbu chat/Topic'ni notifikatsiyalarga bog'laydi (faqat guruh admini). Yangi `/bind` eskisini almashtiradi. |
| `/unbind` | Bog'lanishni o'chiradi. |
| `/status` | Joriy bog'lanishni ko'rsatadi (Chat ID, Topic ID, Created At). |
| `/help` | Barcha komandalar haqida ma'lumot. |

---

## GitLab Webhook sozlash

1. GitLab loyihangizda: **Settings → Webhooks → Add new webhook**.
2. **URL**: `https://<sizning-ochiq-domen>/webhook/gitlab`
3. **Secret token**: `.env` dagi `GITLAB_WEBHOOK_SECRET` bilan **bir xil** qiymat.
4. **Trigger** eventlarni belgilang: Push, Tag push, Merge request, Pipeline,
   Job, Note (comments), Releases.
5. **Add webhook** → **Test → Push events** bilan tekshiring.

Secret noto'g'ri bo'lsa xizmat `403` qaytaradi.

### Qo'llab-quvvatlanadigan eventlar

- **Push** (yangi branch / o'chirilgan branch ham)
- **Tag push** (yaratilgan / o'chirilgan)
- **Merge Request**: opened, updated, approved, merged, closed, reopened
- **Pipeline**: running, success, failed, canceled, skipped
- **Job**: success, failed
- **Release**: created, updated
- **Note**: Merge Request izohlari

Qo'llab-quvvatlanmaydigan eventlar jimgina o'tkazib yuboriladi (`200`), lekin
notifikatsiya yuborilmaydi.

---

## Testlar

Testlar uchun PostgreSQL kerak (`postgres-test`, port `25439`):

```bash
task test                      # postgres-test + pytest
# yoki bitta test:
docker compose up -d postgres-test
ENV=test uv run pytest tests/test_formatters.py -vv
```

Sifat tekshiruvi (CI to'plami):

```bash
task all      # format → deptry → typecheck → testcov
```

Qamrov: GitLab webhook (403 / dispatch), barcha formatterlar (HTML-escape bilan),
`BindingRepository` (bitta aktiv binding), Telegram notifier (Topic bilan/siz, retry).

---

## Troubleshooting

| Muammo | Yechim |
|---|---|
| Bot `/bind` ga javob bermayapti | @BotFather'da **Privacy Mode o'chirilganini** va bot **admin** ekanini tekshiring. |
| Telegram webhook o'rnatilmayapti | `TELEGRAM_WEBHOOK_URL` **HTTPS** va ochiq bo'lishi kerak. `curl https://<url>/health` ishlaydimi? |
| GitLab webhook `403` | GitLab "Secret token" `GITLAB_WEBHOOK_SECRET` bilan mos emas. |
| Container DB'ga ulanmayapti | `.env` da `POSTGRES_HOST` **bo'lmasligi** kerak — Compose uni `postgres` deb beradi. |
| `docker compose` port bandligi | `PORT` (app) yoki `POSTGRES_PORT` ni `.env` da o'zgartiring. |
| Migratsiya xatosi | `cd src && ENV=local uv run alembic upgrade head` ni qo'lda ishlating va logni tekshiring. |
| Notifikatsiya kelmayapti | Guruhda `/status` bilan bog'lanish borligini tekshiring; ilova loglarida "No active binding" bormi? |

---

## Litsenziya

`LICENSE` fayliga qarang.
