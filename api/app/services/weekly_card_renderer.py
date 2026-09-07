from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from api.app.texts.weekly_card import CATALOGS
from PIL import Image, ImageDraw, ImageFilter, ImageFont

MAX_WEEKS = 7

W = 1120
OUTER_X = 34
OUTER_Y = 30
OUTER_W = 1052
CONTENT_X = 64
CONTENT_W = 992

HEADER_TITLE_Y = 124
HEADER_SUBTITLE_Y = 166
HERO_X = CONTENT_X
HERO_Y = 210
HERO_W = CONTENT_W
HERO_H = 205
HISTORY_TITLE_Y = 474
ROWS_Y = 515
ROW_H = 82
ROW_GAP = 10
FOOTER_GAP = 20
FOOTER_H = 125
BOTTOM_PAD = 30

FONT_REGULAR = str(Path(__file__).parents[1] / "assets/DejaVuSans.ttf")
FONT_BOLD = str(Path(__file__).parents[1] / "assets/DejaVuSans-Bold.ttf")

_FONTS = {
    "title": ImageFont.truetype(FONT_BOLD, 50),
    "hero_number": ImageFont.truetype(FONT_BOLD, 86),
    "hero_unit": ImageFont.truetype(FONT_BOLD, 29),
    "hero_prev": ImageFont.truetype(FONT_REGULAR, 21),
    "hero_prev_value": ImageFont.truetype(FONT_BOLD, 21),
    "hero_badge": ImageFont.truetype(FONT_BOLD, 30),
    "section_title": ImageFont.truetype(FONT_BOLD, 34),
    "section_meta": ImageFont.truetype(FONT_REGULAR, 18),
    "footer_value": ImageFont.truetype(FONT_BOLD, 46),
}


def _text_width(text: str, font_key: str) -> float:
    box = _FONTS[font_key].getbbox(text)
    return float(box[2] - box[0])


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _rounded_gradient(
    image: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    """Paint a vertical gradient clipped to a rounded rectangle."""

    left, upper, right, lower = box
    height = lower - upper
    gradient = Image.new("RGB", (right - left, height))
    gradient_draw = ImageDraw.Draw(gradient)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(top, bottom))
        gradient_draw.line((0, y, right - left, y), fill=color)
    mask = Image.new("L", gradient.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *gradient.size), radius=radius, fill=255)
    image.paste(gradient, (left, upper), mask)


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font_key: str,
    fill: str,
    *,
    anchor: str = "ls",
) -> None:
    draw.text(xy, text, font=_FONTS[font_key], fill=fill, anchor=anchor)


def _pct_text(value: float, language: str = "ru") -> str:
    sign = "+" if value > 0 else "−" if value < 0 else ""
    return f"{sign}{abs(value):.1f}%".replace(".", "," if language == "ru" else ".")


@dataclass(frozen=True)
class WeekStat:
    """One calendar week. Pass newest-first. Missing calendar weeks should be total=0."""

    label: str
    total: int


def _card_height(visible_week_count: int) -> tuple[int, int]:
    footer_y = ROWS_Y + visible_week_count * (ROW_H + ROW_GAP) + FOOTER_GAP
    outer_h = footer_y + FOOTER_H + BOTTOM_PAD - OUTER_Y
    image_h = outer_h + OUTER_Y + 30
    return footer_y, image_h


def _row_change(all_weeks: list[WeekStat], visible: list[WeekStat], i: int, language: str = "ru") -> tuple[float | None, str]:
    """Return change for a visible week; 'start' only if this is truly the user's first week."""

    if i < len(visible) - 1:
        older = visible[i + 1].total
    elif len(all_weeks) > len(visible):
        older = all_weeks[len(visible)].total
    else:
        return None, CATALOGS[language]["start"]

    if older == 0:
        return None, "—"

    pct = (visible[i].total - older) / older * 100
    return pct, _pct_text(pct, language)


def render_weekly_card(
    exercise_name: str,
    weeks: Sequence[WeekStat],
    output_png: str | Path,
    language: str = "ru",
) -> None:
    """Render the Repka weekly summary card to PNG using Pillow.

    Rules:
    - up to 7 latest calendar weeks are visible;
    - with >7 weeks, header shows "7 из N недель";
    - the oldest visible week still compares with the hidden 8th week;
    - "старт" is shown only on the actual first tracked week;
    - number/unit, section metadata, hero chip/caption, and footer metadata are
      positioned from measured text widths rather than hard-coded sibling X positions.
    """

    language = language if language in CATALOGS else "en"
    labels = CATALOGS[language]
    if not weeks:
        raise ValueError("At least one week is required")

    while _text_width(exercise_name, "title") > 940:
        exercise_name = exercise_name[:-2].rstrip() + "…"
    all_weeks = list(weeks)
    if any(w.total < 0 for w in all_weeks):
        raise ValueError("Week total cannot be negative")

    visible = all_weeks[:MAX_WEEKS]
    footer_y, image_h = _card_height(len(visible))
    outer_h = image_h - OUTER_Y - 30

    current = visible[0].total
    previous = visible[1].total if len(visible) > 1 else None
    delta = None if previous is None else current - previous
    delta_pct = None if previous in (None, 0) else delta / previous * 100
    best = max(visible, key=lambda w: w.total)
    average = round(sum(w.total for w in visible) / len(visible))
    max_week_value = max(w.total for w in visible)

    image = Image.new("RGB", (W, image_h), "#EAF5FF")
    _rounded_gradient(image, (OUTER_X, OUTER_Y, OUTER_X + OUTER_W, OUTER_Y + outer_h), 42, (255, 255, 255), (247, 251, 255))
    shadow = Image.new("RGBA", image.size)
    ImageDraw.Draw(shadow).rounded_rectangle((OUTER_X, OUTER_Y + 18, OUTER_X + OUTER_W, OUTER_Y + outer_h + 18), radius=42, fill=(107, 143, 179, 46))
    image = Image.alpha_composite(image.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(28))).convert("RGB")
    _rounded_gradient(image, (OUTER_X, OUTER_Y, OUTER_X + OUTER_W, OUTER_Y + outer_h), 42, (255, 255, 255), (247, 251, 255))
    _rounded_gradient(image, (HERO_X, HERO_Y, HERO_X + HERO_W, HERO_Y + HERO_H), 28, (250, 253, 255), (237, 247, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((HERO_X, HERO_Y, HERO_X + HERO_W, HERO_Y + HERO_H), radius=28, outline="#8FC6FF", width=2)

    _draw_text(draw, (84, HEADER_TITLE_Y), exercise_name, "title", "#111827")
    _draw_text(draw, (84, HEADER_SUBTITLE_Y), labels["subtitle"], "hero_prev", "#65758B")
    _draw_text(draw, (98, 247), labels["last"], "hero_prev", "#53637A")
    _draw_text(draw, (98, 364), str(current), "hero_number", "#111827")
    hero_unit_x = 98 + _text_width(str(current), "hero_number") + 12
    _draw_text(draw, (hero_unit_x, 360), labels["reps"], "hero_unit", "#667085")

    if previous is None:
        draw.rounded_rectangle((694, 259, 922, 317), radius=29, fill="#EEF2F7")
        _draw_text(draw, (808, 296), labels["start"], "hero_badge", "#41526B", anchor="ms")
    else:
        chip_text = f"{abs(delta)} ({_pct_text(delta_pct, language) if delta_pct is not None else '—'})"
        chip_w = max(48 + _text_width(chip_text, "hero_badge"), _text_width(labels["previous"], "hero_prev") + _text_width(str(previous), "hero_prev_value") + 44)
        chip_x, chip_y = HERO_X + HERO_W - 30 - chip_w, 259
        if delta < 0:
            hero_bg, hero_text = "#FDE7EA", "#B4232C"
            arrow = [(chip_x + 22, chip_y + 20), (chip_x + 38, chip_y + 20), (chip_x + 30, chip_y + 33)]
            draw.polygon(arrow, fill=hero_text)
        elif delta == 0:
            hero_bg, hero_text = "#EEF2F7", "#41526B"
        else:
            hero_bg, hero_text = "#E4F6E9", "#13733A"
            arrow = [(chip_x + 22, chip_y + 33), (chip_x + 38, chip_y + 33), (chip_x + 30, chip_y + 20)]
            draw.polygon(arrow, fill=hero_text)
        draw.rounded_rectangle((chip_x, chip_y, chip_x + chip_w, chip_y + 58), radius=29, fill=hero_bg)
        if delta == 0:
            draw.rectangle((chip_x + 22, chip_y + 27, chip_x + 38, chip_y + 30), fill=hero_text)
        elif delta is not None:
            draw.polygon(arrow, fill=hero_text)
        _draw_text(draw, (chip_x + 48, chip_y + 37), chip_text, "hero_badge", hero_text)
        caption_w = _text_width(labels["previous"], "hero_prev") + 8 + _text_width(str(previous), "hero_prev_value")
        caption_x = chip_x + chip_w / 2 - caption_w / 2
        _draw_text(draw, (caption_x, 359), labels["previous"], "hero_prev", "#65758B")
        _draw_text(draw, (caption_x + _text_width(labels["previous"], "hero_prev") + 8, 359), str(previous), "hero_prev_value", "#3B4D66")

    history_title = labels["history"]
    _draw_text(draw, (74, HISTORY_TITLE_Y), history_title, "section_title", "#111827")
    if len(all_weeks) > len(visible):
        _draw_text(draw, (74 + _text_width(history_title, "section_title") + 22, HISTORY_TITLE_Y - 4), labels["shown"].format(visible=len(visible), total=len(all_weeks)), "section_meta", "#8492A6")

    bar_colors = ["#8EC8FF", "#FFC89C", "#AEE8C8", "#F2B6D8", "#D1B7F4", "#D8C8BC", "#F0C7EA"]
    for i, week in enumerate(visible):
        y = ROWS_Y + i * (ROW_H + ROW_GAP)
        pct, pct_label = _row_change(all_weeks, visible, i, language)
        badge_fill, badge_text = ("#EEF2F7", "#41526B") if pct is None else (("#E4F6E9", "#13733A") if pct >= 0 else ("#FCE7EA", "#B4232C"))
        draw.rounded_rectangle((CONTENT_X, y, CONTENT_X + CONTENT_W, y + ROW_H), radius=22, fill="#F2F8FF" if i == 0 else "#FFFFFF", outline="#B8D9FF" if i == 0 else "#E7EDF5", width=2 if i == 0 else 1)
        _draw_text(draw, (88, y + 52), week.label, "hero_prev", "#334155")
        _draw_text(draw, (315, y + 54), str(week.total), "hero_unit", "#111827")
        draw.rounded_rectangle((408, y + 35, 833, y + 49), radius=7, fill="#E9EFF5")
        fill_w = 425 * week.total / max_week_value if max_week_value else 0
        if fill_w:
            draw.rounded_rectangle((408, y + 35, 408 + fill_w, y + 49), radius=7, fill=bar_colors[i])
        draw.rounded_rectangle((884, y + 20, 1016, y + 62), radius=21, fill=badge_fill)
        _draw_text(draw, (950, y + 48), pct_label, "hero_prev_value", badge_text, anchor="ms")

    draw.rounded_rectangle((CONTENT_X, footer_y, CONTENT_X + CONTENT_W, footer_y + FOOTER_H), radius=26, fill="#FFFFFF")
    draw.line((560, footer_y + 24, 560, footer_y + FOOTER_H - 24), fill="#E4EAF1", width=1)
    _draw_text(draw, (112, footer_y + 39), labels["best"], "section_meta", "#64748B")
    _draw_text(draw, (112, footer_y + 94), str(best.total), "footer_value", "#111827")
    _draw_text(draw, (112 + _text_width(str(best.total), "footer_value") + 14, footer_y + 92), best.label, "section_meta", "#64748B")
    _draw_text(draw, (604, footer_y + 39), labels["average"], "section_meta", "#64748B")
    _draw_text(draw, (604, footer_y + 94), str(average), "footer_value", "#111827")
    _draw_text(draw, (604 + _text_width(str(average), "footer_value") + 14, footer_y + 92), labels["per_week"], "section_meta", "#64748B")

    output_png = Path(output_png)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png, format="PNG")
