"""English Telegram UI copy."""

# Common screens and notifications
EXERCISES_TITLE = "Your exercises:"
NO_EXERCISES = "You don't have any exercises yet."
WELCOME = (
    "Hi! Here you can quickly log exercises and track your progress."
    "\n\nCreate your first exercise."
)
CHOOSE_EXERCISE = "Choose an exercise:"
EXERCISE_ADDED = "Exercise added"
EXERCISE_NOT_FOUND = "Exercise not found."
REQUEST_EXERCISE_NAME = "Enter the exercise name:"
EMPTY_EXERCISE_NAME = "The name cannot be empty. Try again:"

SCREEN_EXPIRED = "This screen has expired."
INPUT_FINISHED = "Input has already finished."
EDIT_FINISHED = "Editing has already finished."
INPUT_CANCELLED = "Cancelled"
ENTRY_NOT_FOUND = "Entry not found."
DAY_OR_EXERCISE_NOT_FOUND = "Day or exercise not found."
RESTORE_INPUT_FAILED = "Could not restore input. Open the exercise again."
RESTORE_ENTRY_FAILED = "Could not restore the entry."

CHOOSE_DATE = "Choose a date:"
CHOOSE_NEW_DATE = "Choose a new date:"
ENTER_DATE = "Enter a date:\n\n25.08\n25.08.2026\n2026-08-25"
TODAY = "Today"
YESTERDAY = "Yesterday"
DAY_BEFORE_YESTERDAY = "Day before yesterday"

MIN_REPETITIONS = "Minimum is 1."
MAX_REPETITIONS = "Maximum is 10,000."
CHANGES_SAVED = "Changes saved"
ENTRY_DELETED = "Entry deleted"
DATE_CHANGED = "Date changed"
RESULT_ADDED = "Added"
HISTORY_CLEARED = "History cleared"
EXERCISE_PERMANENTLY_DELETED = "Exercise permanently deleted"

# API errors
ACCESS_FORBIDDEN = "Access to the bot is restricted."
BACKEND_UNAVAILABLE = "The service is temporarily unavailable. Try again later."
RESOURCE_NOT_FOUND = "Data not found. Send /start and try again."
RESOURCE_CONFLICT = "The exercise is no longer available."
REQUEST_FAILED = "Could not complete the request. Try again later."

# Keyboards
BUTTON_ADD_EXERCISE = "➕ Add exercise"
BUTTON_SETTINGS = "⚙️ Settings"
BUTTON_CUSTOM_EXERCISE = "Custom exercise"
BUTTON_ADD_RESULT = "➕ Add Result"
BUTTON_STATISTICS = "📊 Statistics"
BUTTON_HISTORY = "📜 History"
BUTTON_EXERCISES = "📋 Exercises"
BUTTON_BACK = "◀️ Back"
BUTTON_BACK_ARROW = "← Back"
BUTTON_CONSTRUCTOR = "🎛 Constructor"
BUTTON_CHANGE_DATE = "📅 Change date"
BUTTON_DATE = "📅 Date"
BUTTON_ENTER_DATE = "✏️ Enter date"
BUTTON_CANCEL = "❌ Cancel"
BUTTON_CANCEL_PLAIN = "Cancel"
BUTTON_REMOVE_SET = "➖ Set"
BUTTON_ADD_SET = "➕ Set"
BUTTON_ADD = "✅ Add"
BUTTON_SAVE = "✅ Save"
BUTTON_EDIT = "✏️ Edit"
BUTTON_DELETE = "🗑 Delete"
BUTTON_CLEAR_HISTORY = "🗑 Clear history"
BUTTON_DELETE_EXERCISE = "Delete exercise"
BUTTON_CONFIRM_CLEAR_HISTORY = "Clear history"
BUTTON_DELETE_PERMANENTLY = "Delete permanently"
BUTTON_CONFIRM_DELETE = "🔴 Yes, delete"
BUTTON_CHANGE_TIMEZONE = "🕐 Change timezone"
BUTTON_OTHER_TIMEZONE = "🌍 Other timezone"
BUTTON_PREVIOUS = "◀️ Previous"
BUTTON_NEXT = "Next ▶️"
BUTTON_CHANGE_LANGUAGE = "🌐 Language"
BUTTON_IMPORT_DATA = "📥 Import data"
BUTTON_IMPORT_MERGE = "🔀 Merge"
BUTTON_IMPORT_REPLACE = "♻️ Replace"
BUTTON_IMPORT = "Import"
BUTTON_REPLACE_AND_IMPORT = "Replace and import"
BUTTON_ENGLISH = "🇬🇧 English"
BUTTON_RUSSIAN = "🇷🇺 Русский"

EXERCISE_PRESETS = (
    "Pull-ups",
    "Push-ups",
    "Squats",
    "Dips",
)

# Input validation
ENTER_RESULT = "Enter a result."
POSITIVE_RESULT_REQUIRED = "The number of sets and repetitions must be positive."
INVALID_RESULT_FORMAT = "Unrecognized format. Examples: 10, 4x10, or 10 9 8."
NUMBER_TOO_LARGE = "The number is too large."
ENTER_DATE_REQUIRED = "Enter a date."
INVALID_DATE = "Unrecognized date. Use 25.08, 25.08.2026, or 2026-08-25."
FUTURE_DATE = "A future date cannot be selected."
SET_NOT_FOUND = "Set not found."
LAST_SET_REQUIRED = "At least one set must remain."


def exercise_name_too_long(max_length: int) -> str:
    return f"The name is too long. Maximum: {max_length} characters."


def sets_count_out_of_range(max_sets: int) -> str:
    return f"The number of sets must be between 1 and {max_sets}."


def repetitions_out_of_range(max_repetitions: int) -> str:
    return f"Repetitions in each set must be between 1 and {max_repetitions:,}."


def too_many_sets(max_sets: int) -> str:
    return f"You can add no more than {max_sets} sets."


# Message templates
def exercise_empty(name: str) -> str:
    return f"🏋️ {name}\n\nNo entries yet."


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
        f"Latest:\n{last_reps}\n"
        f"{last_date}\n\n"
        f"Today: {today_reps}\n"
        f"7 days: {last_7_days_reps}\n"
        f"30 days: {last_30_days_reps}\n"
        f"Total: {total_reps}"
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
        f"Today: {today_reps}\n"
        f"7 days: {last_7_days_reps}\n"
        f"30 days: {last_30_days_reps}\n"
        f"All time: {total_reps}\n\n"
        f"Training days: {active_days}\n"
        f"Entries: {entries}"
    )
    if best_day is not None and best_day_reps is not None:
        value += f"\n\nBest day:\n{best_day} — {best_day_reps}"
    return value


def history_days(name: str, *, has_entries: bool) -> str:
    suffix = "Choose a day:" if has_entries else "No entries yet."
    return f"📜 {name}\n\n{suffix}"


def history_day(name: str, performed_on: str, total_reps: str) -> str:
    return f"🏋️ {name}\n{performed_on}\nDay total: {total_reps}"


def history_entry(
    name: str,
    performed_on: str,
    reps: str,
    total_reps: str,
) -> str:
    return f"🏋️ {name}\n\n{performed_on}\n{reps}\nTotal: {total_reps}"


def delete_confirmation(performed_on: str, reps: str) -> str:
    return f"Delete this entry?\n\n{performed_on}\n{reps}"


def clear_history_confirmation(name: str, entries: str, total_reps: str) -> str:
    return (
        f"Clear all history for {name}?\n\n"
        f"{entries} entries\n{total_reps} reps\n\n"
        "This cannot be undone."
    )


def hard_delete_confirmation(name: str, entries: str, total_reps: str) -> str:
    return (
        f"Delete {name} permanently?\n\n"
        f"{entries} entries\n{total_reps} reps\n\n"
        "The exercise and all its history will be permanently deleted."
    )


def result_saved(name: str, reps: str, total_reps: int, performed_on: str) -> str:
    return (
        f"✅ Added\n\n{name}\n{reps}\n\n"
        f"Total: {total_reps}\nDate: {performed_on}"
    )


def result_input(name: str, performed_on: str) -> str:
    return (
        f"🏋️ {name}\n\nDate: {performed_on}\n\n"
        "Enter a result:\n10\n4x10\n10 9 8 7"
    )


def result_constructor(name: str, performed_on: str, sets: str) -> str:
    return f"🏋️ {name}\n\nDate: {performed_on}\n\nSets:\n{sets}"


def history_constructor(name: str, sets: str) -> str:
    return f"✏️ {name}\n\nSets:\n{sets}"


def settings(timezone: str, language_name: str) -> str:
    return (
        f"⚙️ Settings\n\nTimezone:\n{timezone}\n\n"
        f"Language:\n{language_name}"
    )


CHOOSE_TIMEZONE = "🌍 Timezone\n\nChoose a timezone:"
ENTER_TIMEZONE = (
    "Enter an IANA timezone, for example:\n\n"
    "Asia/Tokyo\nEurope/Berlin\nAmerica/Chicago"
)
ENTER_TIMEZONE_REQUIRED = "Enter an IANA timezone and try again."
INVALID_TIMEZONE = "Timezone not recognized. Enter an IANA timezone and try again."
TIMEZONE_CHANGED = "Timezone changed"
CHOOSE_LANGUAGE = "🌐 Choose a language"
LANGUAGE_CHANGED = "Language changed"
LANGUAGE_ENGLISH = "English"
LANGUAGE_RUSSIAN = "Русский"

IMPORT_SEND_FILE = "📥 Import\n\nSend a .json file (maximum 1 MB)."
IMPORT_JSON_ONLY = "Only .json files are supported."
IMPORT_FILE_TOO_LARGE = "The file is too large. Maximum size is 1 MB."
IMPORT_INVALID_FILE = "The JSON file is invalid or does not match the import format."
IMPORT_CANCELLED = "Import cancelled"


def import_preview(
    *,
    exercises: str,
    entries: str,
    total_reps: str,
    date_from: str,
    date_to: str,
    new_count: str,
    existing_names: list[str],
) -> str:
    value = (
        "📥 Import\n\n"
        f"Exercises: {exercises}\n"
        f"Workout entries: {entries}\n"
        f"Total reps: {total_reps}\n"
        f"Date range: {date_from} — {date_to}\n\n"
        f"New exercises: {new_count}\n"
        f"Existing exercises: {len(existing_names)}"
    )
    if existing_names:
        value += "\n\nExisting:\n" + "\n".join(
            f"• {name}" for name in existing_names
        )
        value += "\n\nHow should existing history be handled?"
    return value


def import_new_exercises_confirmation(
    *,
    exercises: str,
    entries: str,
    total_reps: str,
    date_from: str,
    date_to: str,
    new_count: str,
) -> str:
    return (
        "📥 Import\n\n"
        f"Exercises: {exercises}\n"
        f"Workout entries: {entries}\n"
        f"Total reps: {total_reps}\n"
        f"Date range: {date_from} — {date_to}\n\n"
        f"New exercises to be created: {new_count}"
    )


def import_confirmation(strategy: str, entries: str, existing_count: int) -> str:
    if strategy == "replace":
        return (
            "Replace existing history?\n\n"
            f"History for {existing_count} matching exercises will be permanently "
            f"deleted.\n{entries} imported entries will then be added."
        )
    return (
        "Merge imported data?\n\n"
        "Existing entries will remain.\n"
        f"{entries} new entries will be added.\n\n"
        "Repeated import may create duplicates."
    )


def import_completed(
    *,
    strategy: str,
    created: str,
    updated: str,
    entries: str,
    total_reps: str,
    include_strategy: bool = True,
) -> str:
    strategy_name = "Replace" if strategy == "replace" else "Merge"
    value = "✅ Import completed\n\n"
    if include_strategy:
        value += f"Strategy: {strategy_name}\n\n"
    return value + (
        f"Exercises created: {created}\n"
        f"Existing exercises updated: {updated}\n"
        f"Entries imported: {entries}\n"
        f"Total reps imported: {total_reps}"
    )


def timezone_changed(timezone: str) -> str:
    return f"✅ Timezone changed\n\n{timezone}"


def language_changed(language_name: str) -> str:
    return f"✅ Language changed\n\n{language_name}"
