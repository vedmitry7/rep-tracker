"""Spanish Telegram UI copy."""
from .en import *
LANGUAGE_CODE = "es"
LANGUAGE_NAME = "Español"
LANGUAGE_BUTTON = "🇪🇸 Español"
EXERCISES_TITLE = "🏋️ Repka\n\nElige un ejercicio"
NO_EXERCISES = "🏋️ Repka\n\nAún no hay ejercicios"
BUTTON_SETTINGS = "⚙️ Ajustes"
BUTTON_ADD_EXERCISE = "➕ Añadir ejercicio"
BUTTON_ADD_FIRST_EXERCISE = "➕ Añade tu primer ejercicio"
BUTTON_ADD_RESULT = "➕ Añadir resultado"
BUTTON_STATISTICS = "📊 Estadísticas"
BUTTON_HISTORY = "📜 Historial"
BUTTON_BACK = BUTTON_BACK_ARROW = "← Atrás"
BUTTON_CHANGE_LANGUAGE = "🌐 Idioma"
BUTTON_CHANGE_TIMEZONE = "🌍 Zona horaria"
CHOOSE_LANGUAGE = "🌐 Elige un idioma"
LANGUAGE_CHANGED = "Idioma cambiado"
TODAY, YESTERDAY, DAY_BEFORE_YESTERDAY = "Hoy", "Ayer", "Anteayer"
ENTER_RESULT = "Introduce un resultado."
INVALID_RESULT_FORMAT = "Formato no reconocido. Ejemplos: 10, 4x10 o 10 9 8."
INVALID_DATE = "Fecha no reconocida. Usa 25.08, 25.08.2026 o 2026-08-25."
BACKEND_UNAVAILABLE = "El servicio no está disponible temporalmente. Inténtalo más tarde."
BOT_NAME = "Repka · Registro de entrenamiento"
BOT_SHORT_DESCRIPTION = "Registra ejercicios, sigue tu progreso y recibe informes semanales."
BOT_DESCRIPTION = "🥬 Repka es un registro de ejercicios en Telegram.\n\nRegistra series y repeticiones en una línea, consulta tu progreso y recibe informes semanales."
BOT_COMMANDS = {"menu": "Menú", "settings": "Ajustes", "help": "Ayuda"}
WELCOME = "🥬 ¡Hola! Soy Repka.\n\nGuardo tus entrenamientos y convierto números sencillos en una historia clara de tu progreso.\n\nAñade un ejercicio y envíame un resultado como 16, 4×10 o 12, 10, 8."
HELP = "ℹ️ Ayuda\n\nElige un ejercicio para añadir un resultado, ver estadísticas o abrir el historial.\n\n/menu — ejercicios\n/settings — ajustes"
from ._translations import _apply_button_translations
_apply_button_translations(globals(), LANGUAGE_CODE)

# Messages and templates.  Keep this catalog self-contained: importing the
# English baseline above is only for backwards-compatible key parity, not copy.
EXERCISE_NOT_FOUND = "No se encontró el ejercicio."
REQUEST_EXERCISE_NAME = "Introduce el nombre del ejercicio"
EMPTY_EXERCISE_NAME = "El nombre no puede estar vacío. Inténtalo de nuevo:"
SCREEN_EXPIRED = "Esta pantalla ha caducado."
INPUT_FINISHED = "La introducción ya ha terminado."
EDIT_FINISHED = "La edición ya ha terminado."
INPUT_CANCELLED = "Cancelado"
ENTRY_NOT_FOUND = "No se encontró la entrada."
DAY_OR_EXERCISE_NOT_FOUND = "No se encontró el día o el ejercicio."
RESTORE_INPUT_FAILED = "No se pudo restaurar la introducción. Abre el ejercicio de nuevo."
RESTORE_ENTRY_FAILED = "No se pudo restaurar la entrada."
CHOOSE_DATE = "Elige una fecha:"
CHOOSE_NEW_DATE = "Elige una nueva fecha:"
ENTER_DATE = "Introduce una fecha:\n\n25.08\n25.08.2026\n2026-08-25"
MIN_REPETITIONS = "El mínimo es 1."
MAX_REPETITIONS = "El máximo es 10.000."
CHANGES_SAVED = "Cambios guardados"
ENTRY_DELETED = "Entrada eliminada"
DATE_CHANGED = "Fecha modificada"
RESULT_ADDED = "Añadido"
HISTORY_CLEARED = "Historial borrado"
ACCESS_FORBIDDEN = "El acceso al bot está restringido."
RESOURCE_NOT_FOUND = "No se encontraron datos. Envía /start e inténtalo de nuevo."
RESOURCE_CONFLICT = "El ejercicio ya no está disponible."
DUPLICATE_EXERCISE_NAME = "Ya existe un ejercicio con este nombre."
REQUEST_FAILED = "No se pudo completar la solicitud. Inténtalo de nuevo más tarde."
BUTTON_GENERATE_CARDS = "🖼 Generar tarjetas"
BUTTON_WEEKLY_CARD = "🖼 Tarjeta semanal"


def exercise_name_too_long(max_length: int) -> str:
    return f"El nombre es demasiado largo. Máximo: {max_length} caracteres."


def sets_count_out_of_range(max_sets: int) -> str:
    return f"El número de series debe estar entre 1 y {max_sets}."


def repetitions_out_of_range(max_repetitions: int) -> str:
    return f"Las repeticiones de cada serie deben estar entre 1 y {max_repetitions:,}."


def too_many_sets(max_sets: int) -> str:
    return f"No puedes añadir más de {max_sets} series."


def exercise_empty(name: str) -> str:
    return f"🏋️ {name}\n\n↩️ Último: —\n\n🔥 Hoy — 0\n📅 7 días — 0\n🗓 30 días — 0\n🏆 Total — 0"


def exercise_summary(*, name: str, last_reps: str, last_date: str, today_reps: str,
                     last_7_days_reps: str, last_30_days_reps: str, total_reps: str) -> str:
    return (f"🏋️ {name}\n\n↩️ Último: {last_reps} · {last_date.lower()}\n\n"
            f"🔥 Hoy — {today_reps}\n📅 7 días — {last_7_days_reps}\n"
            f"🗓 30 días — {last_30_days_reps}\n🏆 Total — {total_reps}")


EXERCISE_MANAGEMENT = "🛠 Gestionar ejercicios"
CLEAR_HISTORY_CHOOSE_EXERCISE = "🧹 Borrar historial\n\nElige un ejercicio"
DELETE_EXERCISE_CHOOSE_EXERCISE = "🗑 Eliminar ejercicio\n\nElige un ejercicio"


def statistics(*, name: str, today_reps: str, last_7_days_reps: str,
               last_30_days_reps: str, total_reps: str, active_days: str,
               entries: str, best_day: str | None, best_day_reps: str | None) -> str:
    value = (f"📊 {name}\n\nHoy: {today_reps}\n7 días: {last_7_days_reps}\n"
             f"30 días: {last_30_days_reps}\nTodo el tiempo: {total_reps}\n\n"
             f"Días de entrenamiento: {active_days}\nEntradas: {entries}")
    if best_day is not None and best_day_reps is not None:
        value += f"\n\nMejor día:\n{best_day} — {best_day_reps}"
    return value


def history_days(name: str, *, has_entries: bool) -> str:
    return f"📜 {name}\n\n{'Elige un día:' if has_entries else 'Aún no hay entradas.'}"


def history_day(name: str, performed_on: str, total_reps: str) -> str:
    return f"🏋️ {name}\n{performed_on}\nTotal del día: {total_reps}"


def history_entry(name: str, performed_on: str, reps: str, total_reps: str) -> str:
    return f"🏋️ {name}\n\n{performed_on}\n{reps}\nTotal: {total_reps}"


def delete_confirmation(performed_on: str, reps: str) -> str:
    return f"¿Eliminar esta entrada?\n\n{performed_on}\n{reps}"


def clear_history_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f"¿Borrar todo el historial de {name}?\n\n{entries} entradas\n{total_reps} repeticiones\n\nEsta acción no se puede deshacer."


def clear_history_not_needed(name: str) -> str:
    return f"ℹ️ {name} ya no tiene entradas que borrar."


def history_cleared(name: str, entries: str, total_reps: str) -> str:
    return f"✅ Historial de {name} borrado\n\nEntradas eliminadas: {entries}\nRepeticiones eliminadas: {total_reps}"


def exercise_permanently_deleted(name: str) -> str:
    return f"✅ {name} se eliminó permanentemente"


def hard_delete_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f"¿Eliminar {name} permanentemente?\n\n{entries} entradas\n{total_reps} repeticiones\n\nEl ejercicio y todo su historial se eliminarán permanentemente."


def result_saved(name: str, reps: str, total_reps: int, performed_on: str) -> str:
    return f"✅ Añadido\n\n{name}\n{reps}\n\nTotal: {total_reps}\nFecha: {performed_on}"


def result_input(name: str, performed_on: str) -> str:
    return f"🏋️ {name}\n\nFecha: {performed_on}\n\nIntroduce un resultado:\n10\n4x10\n10 9 8 7"


def result_constructor(name: str, performed_on: str, sets: str) -> str:
    return f"🏋️ {name}\n\nFecha: {performed_on}\n\nSeries:\n{sets}"


def history_constructor(name: str, sets: str) -> str:
    return f"✏️ {name}\n\nSeries:\n{sets}"


def settings(timezone: str, language_name: str) -> str:
    return f"⚙️ Ajustes\n\nZona horaria:\n{timezone}\n\nIdioma:\n{language_name}"


CHOOSE_TIMEZONE = "🌍 Zona horaria\n\nElige una zona horaria:"
ENTER_TIMEZONE = "Introduce una zona horaria IANA, por ejemplo:\n\nAsia/Tokyo\nEurope/Berlin\nAmerica/Chicago"
ENTER_TIMEZONE_REQUIRED = "Introduce una zona horaria IANA e inténtalo de nuevo."
INVALID_TIMEZONE = "No se reconoce la zona horaria. Introduce una zona horaria IANA e inténtalo de nuevo."
TIMEZONE_CHANGED = "Zona horaria modificada"

IMPORT_SEND_FILE = """📥 <b>Importar datos</b>

Sube un archivo JSON con ejercicios y entrenamientos.

El archivo debe usar codificación UTF-8 y no superar 1 MB.

<b>Estructura y ejemplo del archivo</b>
<pre><code>{
  "version": 1,
  "exercises": [
    {"name": "Dominadas", "days": [{"date": "2026-08-01", "entries": [[10], [8, 7]]}]}
  ]
}</code></pre>
"""
IMPORT_JSON_ONLY = "Solo se admiten archivos .json."
IMPORT_FILE_TOO_LARGE = "El archivo es demasiado grande. El tamaño máximo es 1 MB."
IMPORT_INVALID_FILE = "El archivo JSON no es válido o no coincide con el formato de importación."
IMPORT_CANCELLED = "Importación cancelada"


def export_selection(*, selected: int, total: int) -> str:
    value = ("📤 Exportar datos\n\nElige los ejercicios que quieres exportar.\n\n"
             "El archivo incluirá todas las entradas de entrenamiento de los ejercicios seleccionados.\n"
             "Podrás importarlo de nuevo más tarde.\n\n"
             f"Seleccionados: {selected} de {total}")
    return value if selected else value + "\n\nElige al menos un ejercicio."


EXPORT_NO_EXERCISES = "📤 Exportar datos\n\nAún no hay ejercicios para exportar."
EXPORT_FILE_TOO_LARGE = "El archivo supera 1 MB y no se puede importar. Elige menos ejercicios."


def export_completed(*, exercises: str, entries: str) -> str:
    return f"✅ Exportación lista\n\nEjercicios: {exercises}\nEntradas de entrenamiento: {entries}"


def _import_details(exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str) -> str:
    return f"Ejercicios: {exercises}\nEntradas de entrenamiento: {entries}\nTotal de repeticiones: {total_reps}\nRango de fechas: {date_from} — {date_to}\n\nEjercicios nuevos: {new_count}"


def import_preview(*, exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str, existing_names: list[str]) -> str:
    value = "📥 Importar\n\n" + _import_details(exercises, entries, total_reps, date_from, date_to, new_count) + f"\nEjercicios existentes: {len(existing_names)}"
    if existing_names:
        value += "\n\nExistentes:\n" + "\n".join(f"• {name}" for name in existing_names) + "\n\n¿Cómo debe tratarse el historial existente?"
    return value


def import_new_exercises_confirmation(*, exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str) -> str:
    return "📥 Importar\n\n" + _import_details(exercises, entries, total_reps, date_from, date_to, new_count) + f"\nSe crearán ejercicios nuevos: {new_count}"


def import_confirmation(strategy: str, entries: str, existing_count: int) -> str:
    if strategy == "replace":
        return f"¿Reemplazar el historial existente?\n\nEl historial de {existing_count} ejercicios coincidentes se eliminará permanentemente.\nDespués se añadirán {entries} entradas importadas."
    return f"¿Combinar los datos importados?\n\nLas entradas existentes permanecerán.\nSe añadirán {entries} entradas nuevas.\n\nUna importación repetida puede crear duplicados."


def import_completed(*, strategy: str, created: str, updated: str, entries: str, total_reps: str, include_strategy: bool = True) -> str:
    value = "✅ Importación completada\n\n"
    if include_strategy:
        value += f"Estrategia: {'Reemplazar' if strategy == 'replace' else 'Combinar'}\n\n"
    return value + f"Ejercicios creados: {created}\nEjercicios existentes actualizados: {updated}\nEntradas importadas: {entries}\nTotal de repeticiones importadas: {total_reps}"


def timezone_changed(timezone: str) -> str:
    return f"✅ Zona horaria modificada\n\n{timezone}"


def language_changed(language_name: str) -> str:
    return f"✅ Idioma modificado\n\n{language_name}"


def weekly_report_toggle(enabled: bool) -> str:
    return "📅 Informe semanal: activado" if enabled else "📅 Informe semanal: desactivado"


def weekly_report_changed(enabled: bool) -> str:
    return "Informe semanal activado" if enabled else "Informe semanal desactivado"


WEEKLY_NO_DATA = "Este ejercicio aún no tiene datos de semanas completas."
WEEKLY_CARD_FAILED = "No se pudo enviar una de las tarjetas. Inténtalo de nuevo desde el menú del ejercicio."
WEEKLY_LABELS = dict(title="📅 Informe semanal", period="Periodo", total="Esta semana: {total} {unit}", first="Aún no hay una semana completa anterior.", previous="Semana anterior", change="Cambio", active="Días activos", best="Mejor día")


def weekly_reps_unit(total: int) -> str:
    return "repetición" if total == 1 else "repeticiones"


POSITIVE_RESULT_REQUIRED = "El número de series y repeticiones debe ser positivo."
NUMBER_TOO_LARGE = "El número es demasiado grande."
ENTER_DATE_REQUIRED = "Introduce una fecha."
FUTURE_DATE = "No se puede seleccionar una fecha futura."
SET_NOT_FOUND = "No se encontró la serie."
LAST_SET_REQUIRED = "Debe quedar al menos una serie."
