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

# Dynamic screens and notifications.  A complete Kazakh catalog prevents the
# English base module from leaking into message templates.
EXERCISE_NOT_FOUND = "Жаттығу табылмады."
REQUEST_EXERCISE_NAME = "Жаттығу атауын енгізіңіз"
EMPTY_EXERCISE_NAME = "Атауы бос болмауы керек. Қайталап көріңіз:"
SCREEN_EXPIRED = "Бұл экранның мерзімі өтіп кетті."
INPUT_FINISHED = "Енгізу аяқталып қалды."
EDIT_FINISHED = "Өңдеу аяқталып қалды."
INPUT_CANCELLED = "Бас тартылды"
ENTRY_NOT_FOUND = "Жазба табылмады."
DAY_OR_EXERCISE_NOT_FOUND = "Күн не жаттығу табылмады."
RESTORE_INPUT_FAILED = "Енгізуді қалпына келтіру мүмкін болмады. Жаттығуды қайта ашыңыз."
RESTORE_ENTRY_FAILED = "Жазбаны қалпына келтіру мүмкін болмады."
CHOOSE_DATE = "Күнді таңдаңыз:"
CHOOSE_NEW_DATE = "Жаңа күнді таңдаңыз:"
ENTER_DATE = "Күнді енгізіңіз:\n\n25.08\n25.08.2026\n2026-08-25"
MIN_REPETITIONS = "Ең азы — 1."
MAX_REPETITIONS = "Ең көбі — 10 000."
CHANGES_SAVED = "Өзгерістер сақталды"
ENTRY_DELETED = "Жазба жойылды"
DATE_CHANGED = "Күн өзгертілді"
RESULT_ADDED = "Қосылды"
HISTORY_CLEARED = "Тарих тазартылды"
ACCESS_FORBIDDEN = "Ботқа кіру шектелген."
RESOURCE_NOT_FOUND = "Деректер табылмады. /start жіберіп, қайталап көріңіз."
RESOURCE_CONFLICT = "Бұл жаттығу енді қолжетімді емес."
DUPLICATE_EXERCISE_NAME = "Осындай атауы бар жаттығу бұрыннан бар."
REQUEST_FAILED = "Сұрауды аяқтау мүмкін болмады. Кейінірек қайталап көріңіз."
POSITIVE_RESULT_REQUIRED = "Жиындар мен қайталаулар саны оң болуы керек."
NUMBER_TOO_LARGE = "Сан тым үлкен."
ENTER_DATE_REQUIRED = "Күнді енгізіңіз."
FUTURE_DATE = "Болашақ күнді таңдау мүмкін емес."
SET_NOT_FOUND = "Жиын табылмады."
LAST_SET_REQUIRED = "Кемінде бір жиын қалуы керек."


def exercise_name_too_long(max_length: int) -> str:
    return f"Атауы тым ұзын. Ең көбі: {max_length} таңба."


def sets_count_out_of_range(max_sets: int) -> str:
    return f"Жиындар саны 1 мен {max_sets} аралығында болуы керек."


def repetitions_out_of_range(max_repetitions: int) -> str:
    return f"Әр жиындағы қайталаулар 1 мен {max_repetitions:,} аралығында болуы керек."


def too_many_sets(max_sets: int) -> str:
    return f"{max_sets} жиыннан артық қоса алмайсыз."


def exercise_empty(name: str) -> str:
    return f"🏋️ {name}\n\n↩️ Соңғысы: —\n\n🔥 Бүгін — 0\n📅 7 күн — 0\n🗓 30 күн — 0\n🏆 Барлығы — 0"


def exercise_summary(*, name: str, last_reps: str, last_date: str, today_reps: str,
                     last_7_days_reps: str, last_30_days_reps: str, total_reps: str) -> str:
    return (f"🏋️ {name}\n\n↩️ Соңғысы: {last_reps} · {last_date.lower()}\n\n"
            f"🔥 Бүгін — {today_reps}\n📅 7 күн — {last_7_days_reps}\n"
            f"🗓 30 күн — {last_30_days_reps}\n🏆 Барлығы — {total_reps}")


EXERCISE_MANAGEMENT = "🛠 Жаттығуларды басқару"
CLEAR_HISTORY_CHOOSE_EXERCISE = "🧹 Тарихты тазалау\n\nЖаттығуды таңдаңыз"
DELETE_EXERCISE_CHOOSE_EXERCISE = "🗑 Жаттығуды жою\n\nЖаттығуды таңдаңыз"


def statistics(*, name: str, today_reps: str, last_7_days_reps: str,
               last_30_days_reps: str, total_reps: str, active_days: str,
               entries: str, best_day: str | None, best_day_reps: str | None) -> str:
    value = (f"📊 {name}\n\nБүгін: {today_reps}\n7 күн: {last_7_days_reps}\n"
             f"30 күн: {last_30_days_reps}\nБарлығы: {total_reps}\n\n"
             f"Жаттығу күндері: {active_days}\nЖазбалар: {entries}")
    if best_day is not None and best_day_reps is not None:
        value += f"\n\nЕң жақсы күн:\n{best_day} — {best_day_reps}"
    return value


def history_days(name: str, *, has_entries: bool) -> str:
    return f"📜 {name}\n\n{'Күнді таңдаңыз:' if has_entries else 'Әзірге жазбалар жоқ.'}"


def history_day(name: str, performed_on: str, total_reps: str) -> str:
    return f"🏋️ {name}\n{performed_on}\nКүндік жиыны: {total_reps}"


def history_entry(name: str, performed_on: str, reps: str, total_reps: str) -> str:
    return f"🏋️ {name}\n\n{performed_on}\n{reps}\nБарлығы: {total_reps}"


def delete_confirmation(performed_on: str, reps: str) -> str:
    return f"Бұл жазбаны жою керек пе?\n\n{performed_on}\n{reps}"


def clear_history_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f"{name} үшін бүкіл тарихты тазалау керек пе?\n\nЖазбалар: {entries}\nҚайталаулар: {total_reps}\n\nБұл әрекетті кері қайтару мүмкін емес."


def clear_history_not_needed(name: str) -> str:
    return f"ℹ️ {name} жаттығуында тазалайтын жазба жоқ."


def history_cleared(name: str, entries: str, total_reps: str) -> str:
    return f"✅ {name} тарихы тазартылды\n\nЖойылған жазбалар: {entries}\nЖойылған қайталаулар: {total_reps}"


def exercise_permanently_deleted(name: str) -> str:
    return f"✅ {name} біржола жойылды"


def hard_delete_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f"{name} біржола жойылсын ба?\n\nЖазбалар: {entries}\nҚайталаулар: {total_reps}\n\nЖаттығу мен оның бүкіл тарихы біржола жойылады."


def result_saved(name: str, reps: str, total_reps: int, performed_on: str) -> str:
    return f"✅ Қосылды\n\n{name}\n{reps}\n\nБарлығы: {total_reps}\nКүні: {performed_on}"


def result_input(name: str, performed_on: str) -> str:
    return f"🏋️ {name}\n\nКүні: {performed_on}\n\nНәтижені енгізіңіз:\n10\n4x10\n10 9 8 7"


def result_constructor(name: str, performed_on: str, sets: str) -> str:
    return f"🏋️ {name}\n\nКүні: {performed_on}\n\nЖиындар:\n{sets}"


def history_constructor(name: str, sets: str) -> str:
    return f"✏️ {name}\n\nЖиындар:\n{sets}"


def settings(timezone: str, language_name: str) -> str:
    return f"⚙️ Баптаулар\n\nУақыт белдеуі:\n{timezone}\n\nТіл:\n{language_name}"


CHOOSE_TIMEZONE = "🌍 Уақыт белдеуі\n\nУақыт белдеуін таңдаңыз:"
ENTER_TIMEZONE = "IANA уақыт белдеуін енгізіңіз, мысалы:\n\nAsia/Tokyo\nEurope/Berlin\nAmerica/Chicago"
ENTER_TIMEZONE_REQUIRED = "IANA уақыт белдеуін енгізіп, қайталап көріңіз."
INVALID_TIMEZONE = "Уақыт белдеуі танылмады. IANA уақыт белдеуін енгізіп, қайталап көріңіз."
TIMEZONE_CHANGED = "Уақыт белдеуі өзгертілді"
IMPORT_SEND_FILE = "📥 <b>Деректерді импорттау</b>\n\nЖаттығулар мен жаттығу жазбалары бар JSON файлын жүктеңіз.\n\nФайл UTF-8 кодтауында болып, 1 МБ-тан аспауы керек."
IMPORT_JSON_ONLY = "Тек .json файлдары қолдау табады."
IMPORT_FILE_TOO_LARGE = "Файл тым үлкен. Ең үлкен өлшемі — 1 МБ."
IMPORT_INVALID_FILE = "JSON файлы жарамсыз не импорт пішіміне сәйкес келмейді."
IMPORT_CANCELLED = "Импорттан бас тартылды"


def export_selection(*, selected: int, total: int) -> str:
    value = f"📤 Деректерді экспорттау\n\nЭкспорттау үшін жаттығуларды таңдаңыз.\n\nТаңдалды: {selected} / {total}"
    return value if selected else value + "\n\nКемінде бір жаттығуды таңдаңыз."


EXPORT_NO_EXERCISES = "📤 Деректерді экспорттау\n\nЭкспорттауға әзірге жаттығулар жоқ."
EXPORT_FILE_TOO_LARGE = "Файл 1 МБ-тан үлкен, сондықтан импортталмайды. Аз жаттығуды таңдаңыз."


def export_completed(*, exercises: str, entries: str) -> str:
    return f"✅ Экспорт дайын\n\nЖаттығулар: {exercises}\nЖаттығу жазбалары: {entries}"


def import_preview(*, exercises: str, entries: str, total_reps: str, date_from: str,
                   date_to: str, new_count: str, existing_names: list[str]) -> str:
    value = (f"📥 Импорттау\n\nЖаттығулар: {exercises}\nЖаттығу жазбалары: {entries}\nҚайталаулар саны: {total_reps}\n"
             f"Күндер аралығы: {date_from} — {date_to}\n\nЖаңа жаттығулар: {new_count}\nБар жаттығулар: {len(existing_names)}")
    if existing_names:
        value += "\n\nБарлары:\n" + "\n".join(f"• {name}" for name in existing_names)
        value += "\n\nБар тарихты қалай өңдеу керек?"
    return value


def import_new_exercises_confirmation(*, exercises: str, entries: str, total_reps: str,
                                      date_from: str, date_to: str, new_count: str) -> str:
    return (f"📥 Импорттау\n\nЖаттығулар: {exercises}\nЖаттығу жазбалары: {entries}\nҚайталаулар саны: {total_reps}\n"
            f"Күндер аралығы: {date_from} — {date_to}\n\nҚұрылатын жаңа жаттығулар: {new_count}")


def import_confirmation(strategy: str, entries: str, existing_count: int) -> str:
    if strategy == "replace":
        return f"Бар тарихты ауыстыру керек пе?\n\nСәйкес келетін {existing_count} жаттығудың тарихы біржола жойылады.\nОдан кейін {entries} импортталған жазба қосылады."
    return f"Импортталған деректерді біріктіру керек пе?\n\nБар жазбалар қалады.\n{entries} жаңа жазба қосылады.\n\nҚайта импорттау қайталанатын жазбаларды тудыруы мүмкін."


def import_completed(*, strategy: str, created: str, updated: str, entries: str,
                     total_reps: str, include_strategy: bool = True) -> str:
    value = "✅ Импорттау аяқталды\n\n"
    if include_strategy:
        value += f"Стратегия: {'Ауыстыру' if strategy == 'replace' else 'Біріктіру'}\n\n"
    return value + f"Құрылған жаттығулар: {created}\nЖаңартылған бар жаттығулар: {updated}\nИмпортталған жазбалар: {entries}\nИмпортталған қайталаулар: {total_reps}"


def timezone_changed(timezone: str) -> str:
    return f"✅ Уақыт белдеуі өзгертілді\n\n{timezone}"


def language_changed(language_name: str) -> str:
    return f"✅ Тіл өзгертілді\n\n{language_name}"


def weekly_report_toggle(enabled: bool) -> str:
    return "📅 Апталық есеп: қосулы" if enabled else "📅 Апталық есеп: өшірулі"


def weekly_report_changed(enabled: bool) -> str:
    return "Апталық есеп қосылды" if enabled else "Апталық есеп өшірілді"


WEEKLY_NO_DATA = "Бұл жаттығу үшін толық апталар туралы дерек әлі жоқ."
WEEKLY_CARD_FAILED = "Карталардың бірін жіберу мүмкін болмады. Жаттығу мәзірінен қайталап көріңіз."
WEEKLY_LABELS = dict(title="📅 Апталық есеп", period="Кезең", total="Осы апта: {total} {unit}", first="Алдыңғы толық апта әлі жоқ.", previous="Алдыңғы апта", change="Өзгеріс", active="Белсенді күндер", best="Ең жақсы күн")


def weekly_reps_unit(total: int) -> str:
    return "қайталау" if total == 1 else "қайталау"
