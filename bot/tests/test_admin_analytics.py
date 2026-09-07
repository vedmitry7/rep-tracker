from bot.app.api.client import AnalyticsSummary, Retention
from bot.app.handlers.admin import (
    ADMIN_ANALYTICS_INFO,
    _analytics_keyboard,
    _format_analytics_summary,
)


def test_analytics_keyboard_has_all_report_periods() -> None:
    keyboard = _analytics_keyboard()
    buttons = keyboard.inline_keyboard[0]

    assert [button.text for button in buttons] == ["Today", "Last 7 days", "Last 30 days"]
    assert [button.callback_data for button in buttons] == [
        "admin_analytics:1",
        "admin_analytics:7",
        "admin_analytics:30",
    ]
    assert keyboard.inline_keyboard[1][0].text == "Info"
    assert keyboard.inline_keyboard[1][0].callback_data == "admin_analytics_info:show"


def test_analytics_info_explains_every_admin_report_field_in_russian() -> None:
    assert "всего пользователей" in ADMIN_ANALYTICS_INFO
    assert "DAU / WAU / MAU" in ADMIN_ANALYTICS_INFO
    assert "Weekly delivery failures" in ADMIN_ANALYTICS_INFO


def test_analytics_report_is_english_and_formats_empty_cohort() -> None:
    report = _format_analytics_summary(
        AnalyticsSummary(
            period_days=7,
            total_users=12,
            new_users=3,
            active_users=5,
            activated_new_users=2,
            result_entries=9,
            average_entries_per_active_user=1.8,
            feature_opens={
                "stats_opened": 4,
                "weekly_report_opened": 1,
                "import_used": 2,
                "export_used": 3,
            },
            locales={"en": 2, "ru": 10},
            retention={
                "day_2": Retention(cohort_size=4, returned_users=2),
                "day_7": Retention(cohort_size=0, returned_users=0),
                "day_30": Retention(cohort_size=1, returned_users=1),
            },
            blocked_users=1,
            weekly_delivery_failures=2,
        )
    )

    assert "Admin analytics — Last 7 days" in report
    assert "Day 2: 2/4 (50%)" in report
    assert "Day 7: no cohort yet" in report
    assert "Imports used: 2" in report
    assert "Blocked bot users: 1" in report
