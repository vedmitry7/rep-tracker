"""Polish Telegram UI copy."""
from .en import *

LANGUAGE_CODE = "pl"
LANGUAGE_NAME = "Polski"
LANGUAGE_BUTTON = "🇵🇱 Polski"
BOT_NAME = "Repka · Monitor treningów"
BOT_COMMANDS = {"menu": "Menu", "settings": "Ustawienia", "help": "Pomoc"}
BOT_SHORT_DESCRIPTION = "Zapisuj ćwiczenia, śledź postępy i otrzymuj tygodniowe raporty."
BOT_DESCRIPTION = "🥬 Repka to monitor ćwiczeń w Telegramie.\n\nZapisuj serie i powtórzenia w jednym wierszu, śledź postępy i otrzymuj tygodniowe raporty."
EXERCISES_TITLE = "🏋️ Repka\n\nWybierz ćwiczenie"
NO_EXERCISES = "🏋️ Repka\n\nNie ma jeszcze ćwiczeń"
WELCOME = "🥬 Cześć! Jestem Repka.\n\nZapamiętuję Twoje treningi i zamieniam proste liczby w jasny obraz postępów.\n\nDodaj ćwiczenie i wyślij wynik: 16, 4×10 albo 12, 10, 8."
HELP = "ℹ️ Pomoc\n\nWybierz ćwiczenie, aby dodać wynik, zobaczyć statystyki lub otworzyć historię.\n\n/menu — ćwiczenia\n/settings — ustawienia"
BUTTON_SETTINGS = "⚙️ Ustawienia"
BUTTON_ADD_EXERCISE = "➕ Dodaj ćwiczenie"
BUTTON_ADD_FIRST_EXERCISE = "➕ Dodaj pierwsze ćwiczenie"
BUTTON_ADD_RESULT = "➕ Dodaj wynik"
BUTTON_STATISTICS = "📊 Statystyki"
BUTTON_HISTORY = "📜 Historia"
BUTTON_BACK = BUTTON_BACK_ARROW = "← Wstecz"
BUTTON_CHANGE_LANGUAGE = "🌐 Język"
BUTTON_CHANGE_TIMEZONE = "🌍 Strefa czasowa"
CHOOSE_LANGUAGE = "🌐 Wybierz język"
LANGUAGE_CHANGED = "Język zmieniony"
TODAY, YESTERDAY, DAY_BEFORE_YESTERDAY = "Dziś", "Wczoraj", "Przedwczoraj"
ENTER_RESULT = "Wpisz wynik."
INVALID_RESULT_FORMAT = "Nierozpoznany format. Przykłady: 10, 4x10 albo 10 9 8."
INVALID_DATE = "Nierozpoznana data. Użyj 25.08, 25.08.2026 albo 2026-08-25."
BACKEND_UNAVAILABLE = "Usługa jest chwilowo niedostępna. Spróbuj ponownie później."

from ._translations import _apply_button_translations
_apply_button_translations(globals(), LANGUAGE_CODE)
