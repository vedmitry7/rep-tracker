from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory


def render_card(data: dict, language: str) -> bytes:
    # Lazy import keeps ordinary API routes independent of native Cairo loading.
    from api.app.services.weekly_card_renderer import WeekStat, render_weekly_card

    weeks = []
    for item in data["history"]:
        start = date.fromisoformat(item["start"])
        end = start + timedelta(days=6)
        weeks.append(WeekStat(f"{start:%d.%m}–{end:%d.%m}", item["total"]))
    with TemporaryDirectory(prefix="repka-weekly-") as directory:
        path = Path(directory) / "weekly.png"
        render_weekly_card(data["name"], weeks, path, language=language)
        return path.read_bytes()
