# Date localization

Dates that people see in the Telegram UI are rendered by
`bot.app.services.date_format.format_user_date`.

- Russian: `7 сентября 2026`
- English: `Sep 7, 2026`
- Other supported UI languages use their own month names and date order.

Use this formatter for screens, buttons, confirmations, import previews, and
weekly reports. Pass `language=` when rendering outside the current Telegram
update context, such as a background worker. Relative labels such as “Today”
and “Yesterday” remain localized text labels.

Do not use this formatter for API payloads, callback data, JSON export/import,
or export filenames. Those machine-readable values remain ISO 8601
(`YYYY-MM-DD`). The bot continues to accept its documented numeric and ISO date
input formats.
