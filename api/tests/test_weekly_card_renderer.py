from datetime import date, timedelta
from io import BytesIO

import pytest
from PIL import Image

from api.app.services.weekly_card import render_card
from api.app.services import weekly_card_renderer as renderer


@pytest.mark.parametrize("language", ["ru", "en"])
@pytest.mark.parametrize("count", [1, 2, 20])
def test_real_png(language, count):
    data = dict(name="Pull-ups <&> " + "long name " * 30, history=[
        dict(start=(date(2026, 8, 24) - timedelta(weeks=i)).isoformat(), total=354+i*42)
        for i in range(count)])
    png = render_card(data, language)
    im = Image.open(BytesIO(png))
    assert im.format == "PNG" and im.width == 1120
    assert im.height == renderer._card_height(min(count, 7))[1]


def test_hidden_eighth_week_comparison():
    weeks = [renderer.WeekStat(str(i), 100) for i in range(7)] + [renderer.WeekStat("8", 200)]
    assert renderer._row_change(weeks, weeks[:7], 6, "en") == (-50, "−50.0%")
