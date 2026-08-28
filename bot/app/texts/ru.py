"""Russian Telegram UI copy.

This module deliberately contains only user-facing labels and message templates.
Callback values, API paths, provider names, and other protocol strings stay next
to the code that owns them.
"""

# Common screens and notifications
EXERCISES_TITLE = "Твои упражнения:"
NO_EXERCISES = "У тебя пока нет упражнений."
WELCOME = (
    "Привет! Здесь можно быстро записывать упражнения и следить "
    "за прогрессом.\n\nСоздай первое упражнение."
)
CHOOSE_EXERCISE = "Выбери упражнение:"
EXERCISE_ADDED = "Упражнение добавлено"
EXERCISE_NOT_FOUND = "Упражнение не найдено."
REQUEST_EXERCISE_NAME = "Напиши название упражнения:"
EMPTY_EXERCISE_NAME = "Название не должно быть пустым. Попробуй ещё раз:"

SCREEN_EXPIRED = "Экран устарел."
INPUT_FINISHED = "Ввод уже завершён."
EDIT_FINISHED = "Редактирование уже завершено."
INPUT_CANCELLED = "Отменено"
ENTRY_NOT_FOUND = "Запись не найдена."
DAY_OR_EXERCISE_NOT_FOUND = "День или упражнение не найдены."
RESTORE_INPUT_FAILED = "Не удалось восстановить ввод. Открой упражнение ещё раз."
RESTORE_ENTRY_FAILED = "Не удалось восстановить запись."

CHOOSE_DATE = "Выбери дату:"
CHOOSE_NEW_DATE = "Выбери новую дату:"
ENTER_DATE = "Введи дату:\n\n25.08\n25.08.2026\n2026-08-25"
TODAY = "Сегодня"
YESTERDAY = "Вчера"
DAY_BEFORE_YESTERDAY = "Позавчера"

MIN_REPETITIONS = "Минимум — 1."
MAX_REPETITIONS = "Максимум — 10 000."
CHANGES_SAVED = "Изменения сохранены"
ENTRY_DELETED = "Запись удалена"
DATE_CHANGED = "Дата изменена"
RESULT_ADDED = "Добавлено"

# API errors
ACCESS_FORBIDDEN = "Доступ к боту ограничен."
BACKEND_UNAVAILABLE = "Сервис временно недоступен. Попробуй ещё раз позже."
RESOURCE_NOT_FOUND = "Данные не найдены. Отправь /start и попробуй ещё раз."
RESOURCE_CONFLICT = "Упражнение больше недоступно."
REQUEST_FAILED = "Не удалось выполнить запрос. Попробуй ещё раз позже."

# Keyboards
BUTTON_ADD_EXERCISE = "➕ Добавить упражнение"
BUTTON_SETTINGS = "⚙️ Настройки"
BUTTON_CUSTOM_EXERCISE = "Своё упражнение"
BUTTON_ADD_RESULT = "➕ Результат"
BUTTON_STATISTICS = "📊 Статистика"
BUTTON_HISTORY = "📜 История"
BUTTON_EXERCISES = "📋 Упражнения"
BUTTON_BACK = "◀️ Назад"
BUTTON_BACK_ARROW = "← Назад"
BUTTON_CONSTRUCTOR = "🎛 Конструктор"
BUTTON_CHANGE_DATE = "📅 Изменить дату"
BUTTON_DATE = "📅 Дата"
BUTTON_ENTER_DATE = "✏️ Ввести дату"
BUTTON_CANCEL = "❌ Отмена"
BUTTON_CANCEL_PLAIN = "Отмена"
BUTTON_REMOVE_SET = "➖ Подход"
BUTTON_ADD_SET = "➕ Подход"
BUTTON_ADD = "✅ Добавить"
BUTTON_SAVE = "✅ Сохранить"
BUTTON_EDIT = "✏️ Изменить"
BUTTON_DELETE = "🗑 Удалить"
BUTTON_CONFIRM_DELETE = "🔴 Да, удалить"
BUTTON_CHANGE_TIMEZONE = "🕐 Изменить часовой пояс"
BUTTON_OTHER_TIMEZONE = "🌍 Другой часовой пояс"
BUTTON_PREVIOUS = "◀️ Назад"
BUTTON_NEXT = "Далее ▶️"
BUTTON_CHANGE_LANGUAGE = "🌐 Язык"
BUTTON_ENGLISH = "🇬🇧 English"
BUTTON_RUSSIAN = "🇷🇺 Русский"

EXERCISE_PRESETS = (
    "Подтягивания",
    "Отжимания",
    "Приседания",
    "Брусья",
)

# Input validation
ENTER_RESULT = "Введи результат."
POSITIVE_RESULT_REQUIRED = (
    "Количество подходов и повторений должно быть положительным."
)
INVALID_RESULT_FORMAT = "Не понял формат. Примеры: 10, 4x10 или 10 9 8."
NUMBER_TOO_LARGE = "Число слишком большое."
ENTER_DATE_REQUIRED = "Введи дату."
INVALID_DATE = "Не понял дату. Используй 25.08, 25.08.2026 или 2026-08-25."
FUTURE_DATE = "Будущую дату выбрать нельзя."
SET_NOT_FOUND = "Подход не найден."
LAST_SET_REQUIRED = "Должен остаться хотя бы один подход."


def exercise_name_too_long(max_length: int) -> str:
    return f"Название слишком длинное. Максимум {max_length} символов."


def sets_count_out_of_range(max_sets: int) -> str:
    return f"Количество подходов должно быть от 1 до {max_sets}."


def repetitions_out_of_range(max_repetitions: int) -> str:
    upper_bound = f"{max_repetitions:,}".replace(",", " ")
    return f"Повторения в каждом подходе должны быть от 1 до {upper_bound}."


def too_many_sets(max_sets: int) -> str:
    return f"Можно добавить не больше {max_sets} подходов."


# Message templates
def exercise_empty(name: str) -> str:
    return f"🏋️ {name}\n\nЗаписей пока нет."


def exercise_summary(
    *,
    name: str,
    last_reps: str,
    last_date: str,
    today_reps: str,
    last_7_days_reps: str,
    last_30_days_reps: str,
    total_reps: str,
) -> str:
    return (
        f"🏋️ {name}\n\n"
        f"Последняя:\n{last_reps}\n"
        f"{last_date}\n\n"
        f"Сегодня: {today_reps}\n"
        f"7 дней: {last_7_days_reps}\n"
        f"30 дней: {last_30_days_reps}\n"
        f"Всего: {total_reps}"
    )


def statistics(
    *,
    name: str,
    today_reps: str,
    last_7_days_reps: str,
    last_30_days_reps: str,
    total_reps: str,
    active_days: str,
    entries: str,
    best_day: str | None,
    best_day_reps: str | None,
) -> str:
    value = (
        f"📊 {name}\n\n"
        f"Сегодня: {today_reps}\n"
        f"7 дней: {last_7_days_reps}\n"
        f"30 дней: {last_30_days_reps}\n"
        f"За всё время: {total_reps}\n\n"
        f"Тренировочных дней: {active_days}\n"
        f"Записей: {entries}"
    )
    if best_day is not None and best_day_reps is not None:
        value += f"\n\nЛучший день:\n{best_day} — {best_day_reps}"
    return value


def history_days(name: str, *, has_entries: bool) -> str:
    suffix = "Выбери день:" if has_entries else "Записей пока нет."
    return f"📜 {name}\n\n{suffix}"


def history_day(name: str, performed_on: str, total_reps: str) -> str:
    return f"🏋️ {name}\n{performed_on}\nВсего за день: {total_reps}"


def history_entry(
    name: str,
    performed_on: str,
    reps: str,
    total_reps: str,
) -> str:
    return f"🏋️ {name}\n\n{performed_on}\n{reps}\nВсего: {total_reps}"


def delete_confirmation(performed_on: str, reps: str) -> str:
    return f"Удалить запись?\n\n{performed_on}\n{reps}"


def result_saved(name: str, reps: str, total_reps: int, performed_on: str) -> str:
    return (
        f"✅ Добавлено\n\n{name}\n{reps}\n\n"
        f"Всего: {total_reps}\nДата: {performed_on}"
    )


def result_input(name: str, performed_on: str) -> str:
    return (
        f"🏋️ {name}\n\nДата: {performed_on}\n\n"
        "Введи результат:\n10\n4x10\n10 9 8 7"
    )


def result_constructor(name: str, performed_on: str, sets: str) -> str:
    return f"🏋️ {name}\n\nДата: {performed_on}\n\nПодходы:\n{sets}"


def history_constructor(name: str, sets: str) -> str:
    return f"✏️ {name}\n\nПодходы:\n{sets}"


def settings(timezone: str, language_name: str) -> str:
    return (
        f"⚙️ Настройки\n\nЧасовой пояс:\n{timezone}\n\n"
        f"Язык:\n{language_name}"
    )


CHOOSE_TIMEZONE = "🌍 Часовой пояс\n\nВыбери часовой пояс:"
ENTER_TIMEZONE = (
    "Введи IANA timezone, например:\n\n"
    "Asia/Tokyo\nEurope/Berlin\nAmerica/Chicago"
)
ENTER_TIMEZONE_REQUIRED = "Введи IANA timezone и попробуй ещё раз."
INVALID_TIMEZONE = (
    "Не удалось распознать timezone. Введи IANA timezone и попробуй ещё раз."
)
TIMEZONE_CHANGED = "Часовой пояс изменён"
CHOOSE_LANGUAGE = "🌐 Выберите язык"
LANGUAGE_CHANGED = "Язык изменён"
LANGUAGE_ENGLISH = "English"
LANGUAGE_RUSSIAN = "Русский"


def timezone_changed(timezone: str) -> str:
    return f"✅ Часовой пояс изменён\n\n{timezone}"


def language_changed(language_name: str) -> str:
    return f"✅ Язык изменён\n\n{language_name}"
