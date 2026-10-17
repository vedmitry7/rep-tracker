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

## Manual date input

When a user opens manual date entry, the prompt and the invalid-date error show
the user's *current* local date (from `get_user_settings`/`settings.today`) in
the three accepted formats via
`bot.app.services.date_format.manual_date_formats`:

- `ДД.ММ` → `17.10`
- `ДД.ММ.ГГГГ` → `17.10.2026`
- `ГГГГ-ММ-ДД` → `2026-10-17`

The numeric formats are identical in every UI language; only the surrounding
prompt and hint are localized. Manual entry screens also offer a
`InlineKeyboardButton(copy_text=CopyTextButton(...))` button labelled with the
short date, which copies that exact text to the Telegram clipboard without
sending a callback or changing the FSM state.

When manual entry opens (or an entered date is parsed), the bot refreshes
`user_today` so a local midnight rollover does not make the fresh date look like
a future date to the parser.
