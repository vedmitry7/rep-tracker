# Rep Tracker

[![CI](https://github.com/vedmitry7/rep-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/vedmitry7/rep-tracker/actions/workflows/ci.yml)

Telegram-first tracker for quickly recording exercise repetitions.

The main flow is intentionally short:

```text
create an exercise
→ enter 10 / 4x10 / 10 9 8 7
→ choose another date if needed
→ review history and statistics
→ edit or delete entries
```

## Features

- Custom exercises and ready-to-use presets
- Fast text input and an inline button constructor
- Backdated entries
- History grouped by training day
- Per-exercise statistics
- Entry editing and deletion
- User-specific timezone support
- English and Russian UI
- Multi-user identity model

## Architecture

```text
Telegram Bot → FastAPI → PostgreSQL
```

The bot and API live in one repository but run as independent applications. The
bot never connects to PostgreSQL directly. See [docs/architecture.md](docs/architecture.md)
for the key design decisions.

## Tech Stack

- Python 3.11+
- aiogram 3
- FastAPI
- SQLAlchemy 2 async / asyncpg
- PostgreSQL
- Alembic
- Docker Compose
- pytest

## Project Structure

```text
api/                 FastAPI app, database models, services, migrations, tests
bot/                 aiogram app, API client, handlers, keyboards, tests
docs/                architecture notes
docker-compose.yml   local full-stack infrastructure
```

## Local Development

Commands below are run from the repository root.

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Linux/macOS
   source .venv/bin/activate
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```

2. Install API and bot development dependencies:

   ```bash
   pip install -r api/requirements-dev.txt -r bot/requirements-dev.txt
   ```

3. Copy `.env.example` to `.env`, set a PostgreSQL password, and add the token
   received from `@BotFather`:

   ```bash
   cp .env.example .env
   # Windows PowerShell: Copy-Item .env.example .env
   ```

4. Start PostgreSQL and apply migrations:

   ```bash
   docker compose up -d postgres
   alembic upgrade head
   ```

5. Start the API:

   ```bash
   fastapi dev api/app/main.py
   ```

6. In another terminal, start the bot:

   ```bash
   python -m bot.app.main
   ```

7. Run all tests and repository checks:

   ```bash
   pytest -q
   alembic check
   python -m compileall -q api bot
   ```

The API docs are available at `http://127.0.0.1:8000/docs`; the database health
endpoint is `http://127.0.0.1:8000/health/db`.

## Full stack with Docker Compose

After creating `.env`, the API, bot, and PostgreSQL can all be started without
local Python processes:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f api bot postgres
```

The API container applies `alembic upgrade head` before starting Uvicorn. Inside
the Compose network, the API connects to `postgres:5432` and the bot connects to
`http://api:8000`. PostgreSQL is also bound to `127.0.0.1` so the existing
PyCharm development workflow continues to work, while Swagger is available at
`http://127.0.0.1:8000/docs`.

Stop the stack without deleting the named PostgreSQL volume:

```bash
docker compose down
```

## Status

The project is being prepared for its first production release.
