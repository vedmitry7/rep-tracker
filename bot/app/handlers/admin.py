"""Explicit, administrator-only Telegram metadata operations.

These operations deliberately never run during normal bot startup. They modify
Telegram-managed state and can be rate-limited by Telegram.
"""

from collections.abc import Awaitable, Callable

from aiogram import Bot, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import BaseFilter, Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.app.api.client import ApiError, AnalyticsSummary, RepTrackerApi
from bot.app.commands import register_commands
from bot.app.core.config import get_settings
from bot.app.profile import configure_profile_descriptions, configure_profile_names


router = Router(name=__name__)

ADMIN_HELP = """Admin commands

/admin_help — show this message
/admin_update_descriptions — update the bot's full and short Telegram descriptions
/admin_update_names — update localized Telegram bot names
/admin_update_commands — update localized Telegram command menus
/admin_analytics — open product analytics reports

These commands are intentionally manual. They never run when the bot starts."""

ADMIN_ANALYTICS_INFO = """Report fields

• <b>Total</b> — всего пользователей за всё время.
• <b>New</b> — сколько зарегистрировались за выбранный период.
• <b>DAU / WAU / MAU</b> — активные пользователи за сегодня / 7 / 30 дней.
• <b>Activated new users</b> — из новых пользователей сколько успели создать упражнение и добавить хотя бы один результат.
• <b>Results added</b> — сколько записей с результатами добавили за период.
• <b>Average results per logging user</b> — среднее число записей на пользователя, который добавлял результаты.
• <b>Statistics opened</b> — сколько раз открывали экран статистики.
• <b>Weekly reports opened</b> — сколько раз открывали недельные отчёты.
• <b>Imports used / Exports used</b> — количество импортов и экспортов.
• <b>Day 2 / 7 / 30</b> — сколько пользователей из когорты, зарегистрированной 2 / 7 / 30 дней назад, вернулись сегодня. Например: <code>2/4 (50%)</code>.
• <b>Locales</b> — распределение всех пользователей по языкам, например: <code>ru: 50, en: 12</code>.
• <b>Blocked bot users</b> — пользователи, которым Telegram больше не позволяет отправлять сообщения от бота.
• <b>Weekly delivery failures</b> — неуспешные попытки отправить еженедельный отчёт за выбранный период."""


class AnalyticsPeriod(CallbackData, prefix="admin_analytics"):
    days: int


class AnalyticsInfo(CallbackData, prefix="admin_analytics_info"):
    action: str = "show"


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return (
            message.from_user is not None
            and message.from_user.id in get_settings().admin_telegram_ids
        )


@router.message(Command("admin_help"), IsAdmin())
async def admin_help(message: Message) -> None:
    await message.answer(ADMIN_HELP)


@router.message(Command("admin_update_descriptions"), IsAdmin())
async def admin_update_descriptions(message: Message, bot: Bot) -> None:
    await _run_telegram_update(
        message,
        bot,
        configure_profile_descriptions,
        "Telegram descriptions updated.",
    )


@router.message(Command("admin_update_names"), IsAdmin())
async def admin_update_names(message: Message, bot: Bot) -> None:
    await _run_telegram_update(
        message,
        bot,
        configure_profile_names,
        "Telegram bot names updated.",
    )


@router.message(Command("admin_update_commands"), IsAdmin())
async def admin_update_commands(message: Message, bot: Bot) -> None:
    await _run_telegram_update(
        message,
        bot,
        register_commands,
        "Telegram command menus updated.",
    )


@router.message(Command("admin_analytics"), IsAdmin())
async def admin_analytics(message: Message) -> None:
    await message.answer("Admin analytics", reply_markup=_analytics_keyboard())


@router.callback_query(AnalyticsPeriod.filter(), IsAdmin())
async def analytics_report(
    callback: CallbackQuery,
    callback_data: AnalyticsPeriod,
    api_client: RepTrackerApi,
) -> None:
    try:
        summary = await api_client.get_analytics_summary(callback_data.days)
    except ApiError:
        await callback.answer("Analytics API is unavailable.", show_alert=True)
        return

    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            _format_analytics_summary(summary),
            reply_markup=_analytics_keyboard(),
        )


@router.callback_query(AnalyticsInfo.filter(), IsAdmin())
async def analytics_info(callback: CallbackQuery) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(ADMIN_ANALYTICS_INFO, parse_mode="HTML")


def _analytics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Today", callback_data=AnalyticsPeriod(days=1).pack()
                ),
                InlineKeyboardButton(
                    text="Last 7 days", callback_data=AnalyticsPeriod(days=7).pack()
                ),
                InlineKeyboardButton(
                    text="Last 30 days", callback_data=AnalyticsPeriod(days=30).pack()
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Info", callback_data=AnalyticsInfo().pack()
                )
            ],
        ]
    )


def _format_analytics_summary(summary: AnalyticsSummary) -> str:
    title = {1: "Today", 7: "Last 7 days", 30: "Last 30 days"}[summary.period_days]
    active_label = {1: "DAU", 7: "WAU", 30: "MAU"}[summary.period_days]
    retention = "\n".join(
        _format_retention(label, summary.retention[label])
        for label in ("day_2", "day_7", "day_30")
    )
    locales = ", ".join(
        f"{language}: {count}" for language, count in summary.locales.items()
    ) or "No users"
    return (
        f"Admin analytics — {title}\n\n"
        "Users\n"
        f"• Total: {summary.total_users}\n"
        f"• New: {summary.new_users}\n"
        f"• {active_label}: {summary.active_users}\n"
        f"• Activated new users: {summary.activated_new_users}/{summary.new_users}\n\n"
        "Activity\n"
        f"• Results added: {summary.result_entries}\n"
        f"• Average results per logging user: "
        f"{summary.average_entries_per_active_user:.1f}\n\n"
        "Features\n"
        f"• Statistics opened: {summary.feature_opens['stats_opened']}\n"
        f"• Weekly reports opened: {summary.feature_opens['weekly_report_opened']}\n"
        f"• Imports used: {summary.feature_opens['import_used']}\n"
        f"• Exports used: {summary.feature_opens['export_used']}\n\n"
        f"Retention\n{retention}\n\n"
        f"Locales: {locales}\n"
        f"Blocked bot users: {summary.blocked_users}\n"
        f"Weekly delivery failures: {summary.weekly_delivery_failures}"
    )


def _format_retention(label: str, metric) -> str:
    day = label.removeprefix("day_")
    if metric.cohort_size == 0:
        return f"• Day {day}: no cohort yet"
    percent = metric.returned_users / metric.cohort_size * 100
    return (
        f"• Day {day}: {metric.returned_users}/{metric.cohort_size} "
        f"({percent:.0f}%)"
    )


async def _run_telegram_update(
    message: Message,
    bot: Bot,
    operation: Callable[[Bot], Awaitable[None]],
    success_message: str,
) -> None:
    try:
        await operation(bot)
    except TelegramRetryAfter as error:
        await message.answer(
            f"Telegram rate limit. Retry after {error.retry_after} seconds."
        )
    except TelegramAPIError as error:
        await message.answer(f"Telegram API error: {error.message}")
    else:
        await message.answer(success_message)
