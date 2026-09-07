"""Kazakh Telegram UI copy."""
from .en import *

LANGUAGE_CODE = "kk"
LANGUAGE_NAME = "Қазақша"
LANGUAGE_BUTTON = "🇰🇿 Қазақша"
BOT_NAME = "Repka · Жаттығу трекері"
BOT_COMMANDS = {"menu": "Мәзір", "settings": "Баптаулар", "help": "Көмек"}
BOT_SHORT_DESCRIPTION = "Жаттығуларды жазып, ілгерілеуді бақылап, апталық есептер алыңыз."
BOT_DESCRIPTION = "🥬 Repka — Telegram-дағы жаттығу трекері.\n\nЖиындар мен қайталауларды бір жолға жазыңыз, ілгерілеуді бақылаңыз және апталық есептер алыңыз."
EXERCISES_TITLE = "🏋️ Repka\n\nЖаттығуды таңдаңыз"
NO_EXERCISES = "🏋️ Repka\n\nӘзірге жаттығулар жоқ"
WELCOME = "🥬 Сәлем! Мен Repka-мен.\n\nМен жаттығуларыңызды сақтап, қарапайым сандарды ілгерілеуіңіздің анық көрінісіне айналдырамын.\n\nЖаттығуды қосып, 16, 4×10 немесе 12, 10, 8 сияқты нәтиже жіберіңіз."
HELP = "ℹ️ Көмек\n\nНәтиже қосу, статистиканы көру немесе тарихты ашу үшін жаттығуды таңдаңыз.\n\n/menu — жаттығулар\n/settings — баптаулар"
BUTTON_SETTINGS = "⚙️ Баптаулар"
BUTTON_ADD_EXERCISE = "➕ Жаттығу қосу"
BUTTON_ADD_FIRST_EXERCISE = "➕ Алғашқы жаттығуды қосыңыз"
BUTTON_ADD_RESULT = "➕ Нәтиже қосу"
BUTTON_STATISTICS = "📊 Статистика"
BUTTON_HISTORY = "📜 Тарих"
BUTTON_BACK = BUTTON_BACK_ARROW = "← Артқа"
BUTTON_CHANGE_LANGUAGE = "🌐 Тіл"
BUTTON_CHANGE_TIMEZONE = "🌍 Уақыт белдеуі"
CHOOSE_LANGUAGE = "🌐 Тілді таңдаңыз"
LANGUAGE_CHANGED = "Тіл өзгертілді"
TODAY, YESTERDAY, DAY_BEFORE_YESTERDAY = "Бүгін", "Кеше", "Арғы күні"
ENTER_RESULT = "Нәтижені енгізіңіз."
INVALID_RESULT_FORMAT = "Пішім танылмады. Мысалдар: 10, 4x10 немесе 10 9 8."
INVALID_DATE = "Күн танылмады. 25.08, 25.08.2026 немесе 2026-08-25 қолданыңыз."
BACKEND_UNAVAILABLE = "Қызмет уақытша қолжетімсіз. Кейінірек қайталап көріңіз."

from ._translations import _apply_button_translations
_apply_button_translations(globals(), LANGUAGE_CODE)
