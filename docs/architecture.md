# Architecture

## Components

```text
Telegram
   ↓
aiogram bot
   ↓ HTTP
FastAPI
   ↓
SQLAlchemy async / asyncpg
   ↓
PostgreSQL
```

- **Bot** owns Telegram interaction, transient FSM state, input parsing, and UI
  rendering. All application data goes through its HTTP API client.
- **FastAPI** is the application boundary. It resolves identities, enforces
  ownership, applies date/timezone rules, and performs data operations.
- **PostgreSQL** is the source of truth for users, identities, exercises, and
  exercise entries.

## Monorepo

The bot and API are kept in one repository so their contract, tests, migrations,
and local infrastructure evolve together. They are still independent processes
and can be built, restarted, or scaled separately. Sharing a repository does not
give the bot direct database access.

## Identity

```text
provider + external_id → UserIdentity → internal User
```

Telegram user IDs are external identities, not primary application IDs. This
keeps the domain model independent from Telegram and allows another provider or
client to be attached to the same internal user later. Client requests identify
the user with `provider` and `external_id`; an internal `user_id` is never
required as client input or used as an identity credential.

## Data Model

```text
User
├── UserIdentity
└── Exercise
    └── ExerciseEntry
```

- `User` stores account-level settings, including timezone and UI language.
- `UserIdentity` maps an external provider identity to a user.
- `Exercise` belongs to one user.
- `ExerciseEntry` belongs to one exercise and stores all sets in PostgreSQL's
  integer array form:

  ```text
  [10]
  [10, 10, 10, 10]
  [10, 9, 8, 7]
  ```

Ownership is checked in the API service layer through shared identity and owned
resource lookups.

## Dates and Timezone

- `created_at` is the technical, timezone-aware absolute creation timestamp.
- `performed_on` is the user's calendar training day; it is not derived from the
  VPS timezone.
- `User.timezone` is a validated IANA timezone used to determine the user's
  current day and date windows.

The current-day policy is centralized in `api/app/core/dates.py`. A bot instance
passes its configured `DEFAULT_TIMEZONE` only when creating a new user. After
that, the user's stored timezone is authoritative.

## Localization

```text
Telegram language_code
   → default language for a new User
   → User.language
   → localized Telegram UI
```

Telegram maps `ru`/`ru-*` to Russian and `en`/`en-*` to English; every other
code falls back to English. The detected value is used only during user creation.
After that, `User.language` is authoritative and can be changed through user
settings without restarting the bot.

## API Boundary

Telegram, future Web/Mini App clients, and Android clients must use the backend
API instead of connecting to PostgreSQL. This keeps identity resolution,
ownership checks, validation, and timezone behavior consistent for every client.

`provider` and `external_id` resolve identity but are not authentication. For the
first bot-only deployment, the API must remain private to the bot/VPS network. A
public Web, Mini App, or Android API requires a separate authentication layer.

```text
Telegram      ┐
Web / Mini App├──→ same FastAPI backend → PostgreSQL
Android       ┘
```

## Persistence

PostgreSQL runs independently from the applications. In local Compose it stores
data in the named Docker volume `postgres_data`, so recreating the container does
not remove application data. Production backup and recovery procedures are a
deployment concern.
