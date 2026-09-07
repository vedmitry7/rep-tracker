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
- `/admin_analytics` — opens English-only reports for today, the last 7 days, and the last 30 days

Run a command only when its corresponding localized catalog data has changed.

Admin commands, buttons, and reports are intentionally English-only and are not
part of the user-facing localization catalog.

`/admin_analytics` also has an `Info` button. It sends a Russian explanation of
every analytics field, explicitly requested for this help text.
