"""Telegram presentation for immutable weekly-report snapshots."""
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.app.texts import get_text


TELEGRAM_TEXT_LIMIT = 4096


def report_blocks(report: dict) -> list[str]:
    language = report["language"]
    labels = get_text(language, "WEEKLY_LABELS")
    fmt = lambda value: date.fromisoformat(value).strftime("%d.%m")
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
