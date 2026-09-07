# Weekly reports and Telegram commands

## Behaviour

- Calendar weeks run Monday–Sunday. The API uses the existing
  `get_user_today(user.timezone)` policy and `performed_on` calendar dates.
- The report period is the previous Monday–Sunday. It becomes due at Monday
  09:00 in the user's IANA timezone. Before that instant the API does not create
  a `weekly_reports` row. A worker that starts from Tuesday through Saturday
  catches up the latest completed week. Sunday waits for the next Monday, so an
  old report is not sent immediately before a new reporting week starts.
- One Telegram text contains blocks for all non-archived exercises with any
  completed-week history. Exercises with only current-week entries are omitted.
  An entirely empty report is never claimed or sent.
- History starts with the calendar week of the first entry. Missing weeks after
  that are zero, not missing data. A single completed tracked week has no
  comparison. A zero previous total has an absolute delta but no percentage.
- Entries on the same date are added before calculating active days and best
  day. A best-day tie uses the most recent date, matching existing statistics.
- The card uses the supplied `repka_weekly_card_renderer_final.py`, adapted in
  `api/app/services/weekly_card_renderer.py`. It shows at most seven recent weeks,
  compares the seventh with the hidden eighth, and labels truncation only when
  needed. Footer statistics describe the displayed weeks. Long names are fitted
  with an ellipsis; user-provided SVG text is escaped.
- The report button uses its saved snapshot, language and week even after later
  entries or a calendar rollover. The exercise-menu button calculates the latest
  completed week using current data. A deleted exercise is no longer accessible.

## Delivery mechanism and trade-off

When `WEEKLY_REPORTS_ENABLED=true`, the bot starts the delivery worker as a
separate asyncio task in the same bot process and container. It stays separate
from polling handlers in code, but requires no third container. Every 30
seconds it asks the private API to materialize due snapshots, then leases up to
ten pending deliveries at a time. The worker has no database connection. The
API scans Telegram identities with keyset pagination (50 candidates per page),
builds each page with one exercise query and one aggregated entry-total query,
and inserts snapshots with `ON CONFLICT DO NOTHING`.

Migration `20260906_10` adds the immutable snapshot and migration
`20260906_12` adds queue state: `pending`, `processing`, `sent`, `retry` and
`failed`, plus attempts, retry time and a lease token. A unique
`(user_id, week_start)` constraint and PostgreSQL `ON CONFLICT DO NOTHING`
prevent duplicate snapshots. Leasing uses `FOR UPDATE SKIP LOCKED`; several
workers can therefore run without taking the same report.

Delivery is deliberately **at least once**: Telegram `sendMessage` has no
idempotency key. A confirmed send is marked `sent`; a temporary error follows
the 1/5/15/60-minute then 6-hour retry policy, and `TelegramRetryAfter` uses the
server-supplied retry delay. If the worker crashes after Telegram accepts a
message but before API acknowledgement, a rare duplicate is preferable to a
silent loss. Exactly-once delivery is not promised.

The worker sends one Telegram message per second. Long reports are split only
between whole exercise blocks to stay within Telegram's 4096-character limit;
the card button is attached to the final part. Per-exercise image failures
produce a localized message and processing continues with the next exercise.
Each card is a separate photo, sent sequentially; no image queue or cache is
used yet.

The existing private-network API trust model applies to worker endpoints. They
must not be exposed as unauthenticated public API.

Telegram limits a text message to 4096 characters. The worker splits a report
between exercise blocks; an individual oversize block is rejected and retried.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/exercises/{exercise_id}/weekly-card` | `image/png`; requires `provider`, `external_id`; optional `report_id` selects an owned saved report |
| POST | `/weekly-reports/materialize?after_id=0` | Private worker page: create due snapshots and return a next cursor |
| POST | `/weekly-reports/lease` | Atomically lease up to ten pending/retry reports for one worker |
| GET | `/weekly-reports/{report_id}` | Owned saved report, using `provider` + `external_id` |
| POST | `/weekly-reports/{report_id}/delivery` | Lease token + `status: sent/retry`; 204 acknowledgement |

Image generation runs in a thread off the API event loop, with its own temporary
directory, and cleans up the PNG afterward. The response is `Cache-Control:
no-store`. A missing user, exercise, report or completed-week dataset returns
404; banned users receive 403.

## Copy examples

Russian:

```text
📅 Недельный отчёт
Период: 24.08 — 30.08

🏋️ Подтягивания
За неделю: 354 повторения
Прошлая неделя: 396
Изменение: 🔴 ▼ 42 (−10,6%)
Активных дней: 5
```

English:

```text
📅 Weekly report
Period: 24.08 — 30.08

🏋️ Pull-ups
This week: 354 reps
Previous week: 396
Change: 🔴 ▼ 42 (−10.6%)
Active days: 5
```

Growth uses `🟢 ▲`, decline `🔴 ▼`, and unchanged totals `➖`. One-week history
uses `Предыдущей полной недели ещё нет.` / `No previous complete week yet.`
Russian repetition nouns have plural forms. The existing bot text catalogs own
all Telegram copy. API-rendered card copy lives in `api/app/texts/weekly_card.py`
to keep the API independent from the Telegram application.

## Commands

Startup calls `setMyCommands` with exactly `menu`, `settings`, `help` for the
default English menu, plus explicit Russian and English language menus.
`/start` remains registered as an entry handler but is omitted from the command
list. `/menu` and `/start` share the existing exercise-list screen. `/settings`
reuses the settings screen. `/help` shows short localized instructions. All four
commands clear the active FSM flow and are registered ahead of state handlers.
Telegram's language-specific command descriptions follow the Telegram client
language; screen text follows the user's saved Repka language.

## Local dependencies and startup

- API card rendering uses Pillow only. The bundled regular/bold TTFs keep text
  measurement reproducible; their license is included beside them. No Cairo
  runtime or platform-specific setup is needed.
- Use the already-running shared local PostgreSQL, apply `alembic upgrade head`,
  run the API with `python -m fastapi dev api/app/main.py`, then run
  `python -m bot.app.main`. The delivery task starts inside the bot only when
  `WEEKLY_REPORTS_ENABLED=true`.
- Never run a second polling instance with a token already used elsewhere.

## Relevant validation

Targeted modules:

```text
api/tests/test_weekly_report.py
api/tests/test_weekly_card_renderer.py
api/tests/test_weekly_reports_api.py
api/tests/test_dates.py
bot/tests/test_weekly_reports.py
bot/tests/test_commands.py
bot/tests/test_start.py
bot/tests/test_settings_flow.py
bot/tests/test_keyboards.py
bot/tests/test_localization.py
bot/tests/test_exercise_screens.py
bot/tests/test_api_client.py
```

These cover 1/2/20-week histories, missing/zero data, daily aggregation, DST and
local Monday boundaries, Sunday 23:59, Monday 08:59, Monday 09:00, Monday 10:00
restart recovery, already-sent deduplication, two timezone users, RU/EN, actual
PNG rendering, owned snapshots, archive/ban checks, scheduler pagination, send
failures/rate limits, both card buttons, command registration and existing screen
routing. PostgreSQL integration tests run in transactions that are rolled back
after each test; they do not rewrite existing user records.

Additional checks: `alembic check`, `python -m compileall -q api bot`,
`git diff --check`, local `/health/db`, API Docker build and PNG render smoke.
PNG samples for 1/2/20 weeks were visually inspected.

Manual Telegram-client smoke remains: tap both card buttons with a dedicated
development bot, inspect the delivered/compressed photos, check the visible
command menu after switching Telegram language, and observe a real local-week
rollover without advancing the clock in tests. The local startup did successfully
register all three language menus and send/acknowledge a weekly text, then polling
reported another instance using the same token; only our local bot was stopped.

## Changed files

Added:

```text
api/alembic/versions/20260906_10_weekly_reports.py
api/alembic/versions/20260906_12_add_weekly_report_delivery_queue.py
api/app/api/routes/weekly_reports.py
api/app/assets/DejaVuSans.ttf
api/app/assets/DejaVuSans-Bold.ttf
api/app/assets/LICENSE_DEJAVU
api/app/models/weekly_report.py
api/app/schemas/weekly_report.py
api/app/services/weekly_report.py
api/app/services/weekly_card.py
api/app/services/weekly_card_renderer.py
api/app/texts/__init__.py
api/app/texts/weekly_card.py
api/tests/test_weekly_report.py
api/tests/test_weekly_card_renderer.py
api/tests/test_weekly_reports_api.py
bot/app/commands.py
bot/app/handlers/commands.py
bot/app/handlers/weekly_reports.py
bot/app/services/weekly_report.py
bot/app/services/telegram_delivery.py
bot/app/workers/weekly_reports.py
bot/tests/test_commands.py
bot/tests/test_weekly_reports.py
docs/weekly-reports.md
```

Modified:

```text
.env.example
api/Dockerfile
api/requirements.txt
api/app/api/router.py
api/app/models/__init__.py
bot/requirements.txt
bot/app/api/client.py
bot/app/core/config.py
bot/app/main.py
bot/app/handlers/start.py
bot/app/handlers/settings.py
bot/app/keyboards/exercises.py
bot/app/texts/ru.py
bot/app/texts/en.py
bot/tests/test_keyboards.py
README.md
```

Local-only changes: the local DB was migrated to head. A pre-existing duplicate exercise name (ID 1206) was given
the suffix ` (2)` so the previous unique-name migration could run. Both exercises
and their entries were preserved. Original names are recorded in the ignored
`.pytest_cache/local-duplicate-names.json`. No production server or deployment
commands were used, and work remains on `dev`.
