"""Ukrainian Telegram UI copy."""

"""Англійська копія інтерфейсу користувача Telegram."""
LANGUAGE_CODE = 'uk'
LANGUAGE_NAME = 'Українська'
LANGUAGE_BUTTON = '🇺🇦 Українська'
BOT_NAME = 'Repka · Трекер тренувань'
BOT_COMMANDS = {'menu': 'Меню', 'settings': 'Налаштування', 'help': 'Довідка'}
BOT_SHORT_DESCRIPTION = 'Відстежуйте вправи, дивіться свій прогрес і отримуйте щотижневі звіти.'
BOT_DESCRIPTION = '🥬 Репка - трекер тренувань у Telegram.\n\nЖурнал сетів і повторень в одному рядку: 16, 4×10 або 12, 10, 8. Репка зберігає результат, підсумовує ваші повторення за день, тиждень і місяць і показує прогрес для кожної вправи.\n\n📊 Статистика та історія тренувань\n🖼 Варто поділитися щотижневими звітами\n📦 Імпорт та експорт даних'
EXERCISES_TITLE = '🏋️ Repka\n\nВиберіть вправу'
NO_EXERCISES = '🏋️ Repka\n\nВправ ще немає'
WELCOME = '🥬 Привіт! Я Репка.\n\nЯ пам’ятаю ваші тренування та перетворюю прості цифри на чітку історію вашого прогресу.\n\nПочати роботу легко:\n1. Додайте вправу — наприклад, Підтягування.\n2. Після тренування надішліть результат: 16, 4×10 або 12, 10, 8.\n3. Я збережу його і порахую вашу статистику.\n\nЗгодом ви побачите свою історію тренувань, щотижневий і місячний прогрес, а також щотижневі звіти, якими зможете ділитися.\n\nВаші дані можна імпортувати та експортувати — вони ніколи не блокуються в Repka.\n\n👇 Додайте свою першу вправу. Це займе всього кілька секунд.'
HELP = 'ℹ️ Допомога\n\nВиберіть вправу, щоб додати результат, переглянути статистику або відкрити історію.\n\n/menu — вправи\n/settings — налаштування'
EXERCISE_NOT_FOUND = 'Вправа не знайдена.'
REQUEST_EXERCISE_NAME = 'Введіть назву вправи'
EMPTY_EXERCISE_NAME = 'Назва не може бути пустою. Спробуйте знову:'
SCREEN_EXPIRED = 'Термін дії цього екрана минув.'
INPUT_FINISHED = 'Введення вже завершено.'
EDIT_FINISHED = 'Редагування вже закінчено.'
INPUT_CANCELLED = 'Скасовано'
ENTRY_NOT_FOUND = 'Запис не знайдено.'
DAY_OR_EXERCISE_NOT_FOUND = 'День або вправа не знайдено.'
RESTORE_INPUT_FAILED = 'Не вдалося відновити введення. Знову відкрийте вправу.'
RESTORE_ENTRY_FAILED = 'Не вдалося відновити запис.'
CHOOSE_DATE = 'Виберіть дату:'
CHOOSE_NEW_DATE = 'Виберіть нову дату:'
ENTER_DATE = 'Введіть дату:\n\n25.08\n25.08.2026\n2026-08-25'
TODAY = 'Сьогодні'
YESTERDAY = 'вчора'
DAY_BEFORE_YESTERDAY = 'Позавчора'
MIN_REPETITIONS = 'Мінімум 1.'
MAX_REPETITIONS = 'Максимум 10 тис.'
CHANGES_SAVED = 'Зміни збережено'
ENTRY_DELETED = 'Запис видалено'
DATE_CHANGED = 'Дата змінена'
RESULT_ADDED = 'Додано'
HISTORY_CLEARED = 'Історія очищена'
ACCESS_FORBIDDEN = 'Доступ до бота обмежено.'
BACKEND_UNAVAILABLE = 'Послуга тимчасово недоступна. Повторіть спробу пізніше.'
RESOURCE_NOT_FOUND = 'Дані не знайдені. Надішліть /start і повторіть спробу.'
RESOURCE_CONFLICT = 'Вправа більше не доступна.'
DUPLICATE_EXERCISE_NAME = 'Вправа з такою назвою вже існує.'
REQUEST_FAILED = 'Не вдалося виконати запит. Повторіть спробу пізніше.'
BUTTON_ADD_EXERCISE = '➕ Додайте вправи'
BUTTON_ADD_FIRST_EXERCISE = '➕ Додайте свою першу вправу'
BUTTON_SETTINGS = '⚙️ Налаштування'
BUTTON_ADD_RESULT = '➕ Додати результат'
BUTTON_STATISTICS = '📊 Статистика'
BUTTON_HISTORY = '📜 Історія'
BUTTON_EXERCISES = '← Вправи'
BUTTON_BACK = '← Назад'
BUTTON_BACK_ARROW = '← Назад'
BUTTON_CONSTRUCTOR = '🎛 Конструктор'
BUTTON_CHANGE_DATE = '📅 Змінити дату'
BUTTON_DATE = '📅 Дата'
BUTTON_ENTER_DATE = '✏️ Введіть дату'
BUTTON_CANCEL = '❌ Скасувати'
BUTTON_CANCEL_PLAIN = 'Скасувати'
BUTTON_REMOVE_SET = '➖ Набір'
BUTTON_ADD_SET = '➕ Набір'
BUTTON_ADD = '✅ Додати'
BUTTON_SAVE = '✅ Економте'
BUTTON_EDIT = '✏️ Редагувати'
BUTTON_DELETE = '🗑 Видалити'
BUTTON_CLEAR_HISTORY = '🧹 Очистити історію'
BUTTON_DELETE_EXERCISE = '🗑 Видалити вправу'
BUTTON_CONFIRM_CLEAR_HISTORY = '🧹 Очистити історію'
BUTTON_DELETE_PERMANENTLY = '🗑 Видалити остаточно'
BUTTON_CONFIRM_DELETE = '🔴 Так, видалити'
BUTTON_CHANGE_TIMEZONE = '🌍 Часовий пояс'
BUTTON_OTHER_TIMEZONE = '🌍 Інший часовий пояс'
BUTTON_PREVIOUS = '◀️ Попередній'
BUTTON_NEXT = 'Далі ▶️'
BUTTON_CHANGE_LANGUAGE = '🌐 Мова'
BUTTON_IMPORT_DATA = '📥 Імпорт даних'
BUTTON_EXPORT_DATA = '📤 Експорт даних'
BUTTON_EXERCISE_MANAGEMENT = '🛠 Керуйте вправами'
BUTTON_IMPORT_MERGE = '🔀 Об’єднати'
BUTTON_IMPORT_REPLACE = '♻️ Замінити'
BUTTON_IMPORT = 'Імпорт'
BUTTON_REPLACE_AND_IMPORT = 'Замінити та імпортувати'
BUTTON_EXPORT = '📤 Експорт'
ENTER_RESULT = 'Введіть результат.'
POSITIVE_RESULT_REQUIRED = 'Кількість підходів і повторень має бути позитивним.'
INVALID_RESULT_FORMAT = 'Нерозпізнаний формат. Приклади: 10, 4x10 або 10 9 8.'
NUMBER_TOO_LARGE = 'Завелике число.'
ENTER_DATE_REQUIRED = 'Введіть дату.'
INVALID_DATE = 'Нерозпізнана дата. Використовуйте 25.08, 25.08.2026 або 2026-08-25.'
FUTURE_DATE = 'Майбутню дату вибрати неможливо.'
SET_NOT_FOUND = 'Набір не знайдено.'
LAST_SET_REQUIRED = 'Повинен залишитися хоча б один набір.'

def exercise_name_too_long(max_length: int) -> str:
    return f'Назва занадто довга. Максимум: {max_length} персонажів.'

def sets_count_out_of_range(max_sets: int) -> str:
    return f'Кількість наборів має бути від 1 до {max_sets}.'

def repetitions_out_of_range(max_repetitions: int) -> str:
    return f'Кількість повторів у кожному підході має бути від 1 до {max_repetitions:,}.'

def too_many_sets(max_sets: int) -> str:
    return f'Ви можете додати не більше ніж {max_sets} набори.'

def exercise_empty(name: str) -> str:
    return f'🏋️ {name}\n\n↩️ Останні: —\n\n🔥 Сьогодні — 0\n📅 7 днів — 0\n🗓 30 днів — 0\n🏆 Разом — 0'

def exercise_summary(*, name: str, last_reps: str, last_date: str, today_reps: str, last_7_days_reps: str, last_30_days_reps: str, total_reps: str) -> str:
    return f'🏋️ {name}\n\n↩️ Останні: {last_reps} · {last_date.lower()}\n\n🔥 Сьогодні — {today_reps}\n📅 7 днів — {last_7_days_reps}\n🗓 30 днів — {last_30_days_reps}\n🏆 Всього — {total_reps}'
EXERCISE_MANAGEMENT = '🛠 Керуйте вправами'
CLEAR_HISTORY_CHOOSE_EXERCISE = '🧹 Очистити історію\n\nВиберіть вправу'
DELETE_EXERCISE_CHOOSE_EXERCISE = '🗑 Видалити вправу\n\nВиберіть вправу'

def statistics(*, name: str, today_reps: str, last_7_days_reps: str, last_30_days_reps: str, total_reps: str, active_days: str, entries: str, best_day: str | None, best_day_reps: str | None) -> str:
    value = f'📊 {name}\n\nСьогодні: {today_reps}\n7 днів: {last_7_days_reps}\n30 днів: {last_30_days_reps}\nЗа весь час: {total_reps}\n\nДні тренувань: {active_days}\nЗаписи: {entries}'
    if best_day is not None and best_day_reps is not None:
        value += f'\n\nНайкращий день:\n{best_day} — {best_day_reps}'
    return value

def history_days(name: str, *, has_entries: bool) -> str:
    suffix = 'Виберіть день:' if has_entries else 'Записів ще немає.'
    return f'📜 {name}\n\n{suffix}'

def history_day(name: str, performed_on: str, total_reps: str) -> str:
    return f'🏋️ {name}\n{performed_on}\nУсього за день: {total_reps}'

def history_entry(name: str, performed_on: str, reps: str, total_reps: str) -> str:
    return f'🏋️ {name}\n\n{performed_on}\n{reps}\nВсього: {total_reps}'

def delete_confirmation(performed_on: str, reps: str) -> str:
    return f'Видалити цей запис?\n\n{performed_on}\n{reps}'

def clear_history_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f'Очистити всю історію для {name}?\n\n{entries} записи\n{total_reps} повторень\n\nЦе неможливо скасувати.'

def clear_history_not_needed(name: str) -> str:
    return f'ℹ️ {name} вже не має записів для очищення.'

def history_cleared(name: str, entries: str, total_reps: str) -> str:
    return f'✅ Історія для {name} очищено\n\nВидалені записи: {entries}\nВилучено повтори: {total_reps}'

def exercise_permanently_deleted(name: str) -> str:
    return f'✅ {name} було остаточно видалено'

def hard_delete_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f'Видалити {name} постійно?\n\n{entries} записи\n{total_reps} повторень\n\nВправа та вся її історія буде остаточно видалено.'

def result_saved(name: str, reps: str, total_reps: int, performed_on: str) -> str:
    return f'✅ Додано\n\n{name}\n{reps}\n\nВсього: {total_reps}\nДата: {performed_on}'

def result_input(name: str, performed_on: str) -> str:
    return f'🏋️ {name}\n\nДата: {performed_on}\n\nВведіть результат:\n10\n4x10\n10 9 8 7'

def result_constructor(name: str, performed_on: str, sets: str) -> str:
    return f'🏋️ {name}\n\nДата: {performed_on}\n\nнабори:\n{sets}'

def history_constructor(name: str, sets: str) -> str:
    return f'✏️{name}\n\nнабори:\n{sets}'

def settings(timezone: str, language_name: str) -> str:
    return f'⚙️ Налаштування\n\nчасовий пояс:\n{timezone}\n\nмова:\n{language_name}'
CHOOSE_TIMEZONE = '🌍 Часовий пояс\n\nВиберіть часовий пояс:'
ENTER_TIMEZONE = 'Введіть часовий пояс IANA, наприклад:\n\nАзія/Токіо\nЄвропа/Берлін\nАмерика/Чикаго'
ENTER_TIMEZONE_REQUIRED = 'Введіть часовий пояс IANA та повторіть спробу.'
INVALID_TIMEZONE = 'Часовий пояс не розпізнано. Введіть часовий пояс IANA та повторіть спробу.'
TIMEZONE_CHANGED = 'Часовий пояс змінено'
CHOOSE_LANGUAGE = '🌐 Виберіть мову'
LANGUAGE_CHANGED = 'Мова змінена'
IMPORT_SEND_FILE = '📥 <b>Імпорт даних</b>\n\nЗавантажте файл JSON із вправами та тренуваннями.\n\nФайл має використовувати кодування UTF-8 і бути не більшим за 1 Мб.'
IMPORT_JSON_ONLY = 'Підтримуються лише файли .json.'
IMPORT_FILE_TOO_LARGE = 'Файл завеликий. Максимальний розмір – 1 Мб.'
IMPORT_INVALID_FILE = 'Файл JSON недійсний або не відповідає формату імпорту.'
IMPORT_CANCELLED = 'Імпорт скасовано'

def export_selection(*, selected: int, total: int) -> str:
    value = f'📤 Експорт даних\n\nВиберіть вправи для експорту.\n\nФайл міститиме всі записи тренувань для вибраних вправ.\nВи можете імпортувати файл пізніше.\n\nВибрано: {selected} з {total}'
    if selected == 0:
        value += '\n\nВиберіть хоча б одну вправу.'
    return value
EXPORT_NO_EXERCISES = '📤 Експорт даних\n\nЩе немає вправ для експорту.'
EXPORT_FILE_TOO_LARGE = 'Розмір файлу перевищує 1 МБ, тому його неможливо імпортувати. Вибирайте менше вправ.'

def export_completed(*, exercises: str, entries: str) -> str:
    return f'✅ Готовий до експорту\n\nВправи: {exercises}\nЗаписи про тренування: {entries}'

def import_preview(*, exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str, existing_names: list[str]) -> str:
    value = f'📥 Імпорт\n\nВправи: {exercises}\nЗаписи про тренування: {entries}\nЗагальна кількість повторень: {total_reps}\nДіапазон дат: {date_from} — {date_to}\n\nНові вправи: {new_count}\nІснуючі вправи: {len(existing_names)}'
    if existing_names:
        value += '\n\nІснуючі:\n' + '\n'.join((f'•{name}' for name in existing_names))
        value += '\n\nЯк слід обробляти існуючу історію?'
    return value

def import_new_exercises_confirmation(*, exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str) -> str:
    return f'📥 Імпорт\n\nВправи: {exercises}\nЗаписи про тренування: {entries}\nЗагальна кількість повторень: {total_reps}\nДіапазон дат: {date_from} — {date_to}\n\nБудуть створені нові вправи: {new_count}'

def import_confirmation(strategy: str, entries: str, existing_count: int) -> str:
    if strategy == 'replace':
        return f'Замінити наявну історію?\n\nІсторія для {existing_count} відповідні вправи буде остаточно видалено.\n{entries} буде додано імпортовані записи.'
    return f'Об’єднати імпортовані дані?\n\nІснуючі записи залишаться.\n{entries} будуть додані нові записи.\n\nПовторний імпорт може створити дублікати.'

def import_completed(*, strategy: str, created: str, updated: str, entries: str, total_reps: str, include_strategy: bool=True) -> str:
    strategy_name = 'Замінити' if strategy == 'replace' else 'Об’єднати'
    value = '✅ Імпорт завершено\n\n'
    if include_strategy:
        value += f'Стратегія: {strategy_name}\n\n'
    return value + f'Створено вправи: {created}\nІснуючі вправи оновлено: {updated}\nІмпортовані записи: {entries}\nЗагальна кількість імпортованих повторень:{total_reps}'

def timezone_changed(timezone: str) -> str:
    return f'✅ Змінено часовий пояс{timezone}'

def language_changed(language_name: str) -> str:
    return f'✅ Мова змінена\n\n{language_name}'
BUTTON_GENERATE_CARDS = '🖼 Створення карток'
BUTTON_WEEKLY_CARD = '🖼 Тижнева картка'

def weekly_report_toggle(enabled: bool) -> str:
    return '📅 Тижневий звіт: на' if enabled else '📅 Тижневий звіт: викл'

def weekly_report_changed(enabled: bool) -> str:
    return 'Щотижневий звіт увімкнено' if enabled else 'Щотижневий звіт вимкнено'
WEEKLY_NO_DATA = 'Ця вправа ще не має даних для повних тижнів.'
WEEKLY_CARD_FAILED = 'Не вдалося надіслати одну з карток. Спробуйте ще раз із меню вправ.'
WEEKLY_LABELS = dict(title='📅 Щотижневий звіт', period='Крапка', total='Цього тижня: {total} {unit}', first='Попереднього повного тижня ще немає.', previous='Попередній тиждень', change='Зміна', active='Активні дні', best='Найкращий день')

def weekly_reps_unit(total: int) -> str:
    return 'представник' if total == 1 else 'повторень'
