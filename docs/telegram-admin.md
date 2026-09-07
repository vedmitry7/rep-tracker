# Telegram administration

Telegram profile and command-menu methods change remote Telegram state and may be
rate-limited. They must never be called as part of normal bot startup, polling, or
ordinary user flows.

The bot exposes the following one-off commands only to IDs listed in local
`ADMIN_TELEGRAM_IDS`:

- `/admin_help`
- `/admin_update_descriptions`
- `/admin_update_names`
- `/admin_update_commands`

Run a command only when its corresponding localized catalog data has changed.
