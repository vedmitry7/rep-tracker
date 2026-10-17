"""Telegram presentation for immutable weekly-report snapshots."""
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.app.texts import get_text
from bot.app.services.date_format import format_user_date


TELEGRAM_TEXT_LIMIT = 4096


def report_blocks(report: dict) -> list[str]:
    language = report["language"]
    labels = get_text(language, "WEEKLY_LABELS")
    fmt = lambda value: format_user_date(date.fromisoformat(value), language=language)
    blocks = [f"{labels['title']}\n{labels['period']}: {fmt(report['week_start'])} — {fmt(report['week_end'])}"]
    for item in report["exercises"]:
        lines = [f"🏋️ {item['name']}", labels["total"].format(
            total=item["total"], unit=get_text(language, "weekly_reps_unit", item["total"]))]
        if item["previous"] is None:
            lines.append(labels["first"])
        else:
            lines.append(f"{labels['previous']}: {item['previous']}")
            delta = item["delta"]
            indicator = "🟢 ▲" if delta > 0 else "🔴 ▼" if delta < 0 else "➖"
            percent = "—" if item["percent"] is None else f"{abs(item['percent']):.1f}%"
            if language == "ru":
                percent = percent.replace(".", ",")
            if item["percent"]:
                percent = ("+" if delta > 0 else "−") + percent
            lines.append(f"{labels['change']}: {indicator} {abs(delta)} ({percent})")
        lines.append(f"{labels['active']}: {item['active_days']}")
        blocks.append("\n".join(lines))
    return blocks


def summary_text(report: dict) -> str:
    return "\n\n".join(report_blocks(report))


def split_summary(report: dict) -> list[str]:
    """Keep whole exercise blocks together under Telegram's 4096-character limit."""
    messages: list[str] = []
    current = ""
    for block in report_blocks(report):
        if len(block) > TELEGRAM_TEXT_LIMIT:
            raise ValueError("A weekly report block exceeds Telegram's text limit")
        candidate = block if not current else f"{current}\n\n{block}"
        if current and len(candidate) > TELEGRAM_TEXT_LIMIT:
            messages.append(current)
            current = block
        else:
            current = candidate
    if current:
        messages.append(current)
    return messages


def disabled_notification(report: dict) -> str | None:
    """One combined message for every exercise disabled in this snapshot."""
    items = report.get("disabled_exercises") or []
    if not items:
        return None
    language = report["language"]
    return "\n\n".join(
        get_text(language, "weekly_report_auto_disabled", item["name"])
        for item in items
    )


def split_disabled_notifications(report: dict) -> list[str]:
    """Combine notices while keeping each Telegram message within its limit."""
    items = report.get("disabled_exercises") or []
    messages: list[str] = []
    current = ""
    for item in items:
        notice = get_text(report["language"], "weekly_report_auto_disabled", item["name"])
        candidate = f"{current}\n\n{notice}" if current else notice
        if len(candidate) > TELEGRAM_TEXT_LIMIT and current:
            messages.append(current)
            current = notice
        else:
            current = candidate
    if current:
        messages.append(current)
    return messages


def report_keyboard(report: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(report["language"], "BUTTON_GENERATE_CARDS"),
                    callback_data=f"weekly:{report['id']}",
                    style="primary",
                )
            ]
        ]
    )
