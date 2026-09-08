"""French Telegram UI copy."""
from .en import *

LANGUAGE_CODE = "fr"
LANGUAGE_NAME = "Français"
LANGUAGE_BUTTON = "🇫🇷 Français"
BOT_NAME = "Repka · Suivi d’entraînement"
BOT_COMMANDS = {"menu": "Menu", "settings": "Paramètres", "help": "Aide"}
BOT_SHORT_DESCRIPTION = "Suivez vos exercices, vos progrès et recevez des rapports hebdomadaires."
BOT_DESCRIPTION = "🥬 Repka est un suivi d’exercices dans Telegram.\n\nEnregistrez vos séries et répétitions sur une ligne, suivez vos progrès et recevez des rapports hebdomadaires."
EXERCISES_TITLE = "🏋️ Repka\n\nChoisissez un exercice"
NO_EXERCISES = "🏋️ Repka\n\nAucun exercice pour le moment"
WELCOME = "🥬 Bonjour ! Je suis Repka.\n\nJe mémorise vos entraînements et transforme de simples chiffres en une vision claire de vos progrès.\n\nAjoutez un exercice et envoyez un résultat : 16, 4×10 ou 12, 10, 8."
HELP = "ℹ️ Aide\n\nChoisissez un exercice pour ajouter un résultat, voir les statistiques ou ouvrir l’historique.\n\n/menu — exercices\n/settings — paramètres"
BUTTON_SETTINGS = "⚙️ Paramètres"
BUTTON_ADD_EXERCISE = "➕ Ajouter un exercice"
BUTTON_ADD_FIRST_EXERCISE = "➕ Ajoutez votre premier exercice"
BUTTON_ADD_RESULT = "➕ Ajouter un résultat"
BUTTON_STATISTICS = "📊 Statistiques"
BUTTON_HISTORY = "📜 Historique"
BUTTON_BACK = BUTTON_BACK_ARROW = "← Retour"
BUTTON_CHANGE_LANGUAGE = "🌐 Langue"
BUTTON_CHANGE_TIMEZONE = "🌍 Fuseau horaire"
CHOOSE_LANGUAGE = "🌐 Choisissez une langue"
LANGUAGE_CHANGED = "Langue modifiée"
TODAY, YESTERDAY, DAY_BEFORE_YESTERDAY = "Aujourd’hui", "Hier", "Avant-hier"
ENTER_RESULT = "Saisissez un résultat."
INVALID_RESULT_FORMAT = "Format non reconnu. Exemples : 10, 4x10 ou 10 9 8."
INVALID_DATE = "Date non reconnue. Utilisez 25.08, 25.08.2026 ou 2026-08-25."
BACKEND_UNAVAILABLE = "Le service est temporairement indisponible. Réessayez plus tard."

from ._translations import _apply_button_translations
_apply_button_translations(globals(), LANGUAGE_CODE)

# Dynamic screens and notifications
EXERCISE_NOT_FOUND = "Exercice introuvable."
REQUEST_EXERCISE_NAME = "Saisissez le nom de l’exercice"
EMPTY_EXERCISE_NAME = "Le nom ne peut pas être vide. Réessayez :"
SCREEN_EXPIRED = "Cet écran a expiré."
INPUT_FINISHED = "La saisie est déjà terminée."
EDIT_FINISHED = "La modification est déjà terminée."
INPUT_CANCELLED = "Annulé"
ENTRY_NOT_FOUND = "Entrée introuvable."
DAY_OR_EXERCISE_NOT_FOUND = "Jour ou exercice introuvable."
CHOOSE_DATE = "Choisissez une date :"
CHOOSE_NEW_DATE = "Choisissez une nouvelle date :"
ENTER_DATE = "Saisissez une date :\n\n25.08\n25.08.2026\n2026-08-25"
MIN_REPETITIONS = "Le minimum est de 1."
MAX_REPETITIONS = "Le maximum est de 10 000."
CHANGES_SAVED = "Modifications enregistrées"
ENTRY_DELETED = "Entrée supprimée"
DATE_CHANGED = "Date modifiée"
RESULT_ADDED = "Ajouté"
HISTORY_CLEARED = "Historique effacé"
ACCESS_FORBIDDEN = "L’accès au bot est restreint."
RESOURCE_NOT_FOUND = "Données introuvables. Envoyez /start puis réessayez."
RESOURCE_CONFLICT = "Cet exercice n’est plus disponible."
DUPLICATE_EXERCISE_NAME = "Un exercice porte déjà ce nom."
REQUEST_FAILED = "Impossible d’effectuer la demande. Réessayez plus tard."

def exercise_name_too_long(max_length: int) -> str:
    return f"Le nom est trop long. Maximum : {max_length} caractères."

def sets_count_out_of_range(max_sets: int) -> str:
    return f"Le nombre de séries doit être compris entre 1 et {max_sets}."

def repetitions_out_of_range(max_repetitions: int) -> str:
    return f"Les répétitions de chaque série doivent être comprises entre 1 et {max_repetitions:,}."

def too_many_sets(max_sets: int) -> str:
    return f"Vous ne pouvez pas ajouter plus de {max_sets} séries."

def exercise_empty(name: str) -> str:
    return f"🏋️ {name}\n\n↩️ Dernier : —\n\n🔥 Aujourd’hui — 0\n📅 7 jours — 0\n🗓 30 jours — 0\n🏆 Total — 0"

def exercise_summary(**v: str) -> str:
    return f"🏋️ {v['name']}\n\n↩️ Dernier : {v['last_reps']} · {v['last_date'].lower()}\n\n🔥 Aujourd’hui — {v['today_reps']}\n📅 7 jours — {v['last_7_days_reps']}\n🗓 30 jours — {v['last_30_days_reps']}\n🏆 Total — {v['total_reps']}"


EXERCISE_MANAGEMENT = "🛠 Gérer les exercices"
CLEAR_HISTORY_CHOOSE_EXERCISE = "🧹 Effacer l’historique\n\nChoisissez un exercice"
DELETE_EXERCISE_CHOOSE_EXERCISE = "🗑 Supprimer un exercice\n\nChoisissez un exercice"


def statistics(**v: str | None) -> str:
    value = (
        f"📊 {v['name']}\n\nAujourd’hui : {v['today_reps']}\n"
        f"7 jours : {v['last_7_days_reps']}\n30 jours : {v['last_30_days_reps']}\n"
        f"Depuis le début : {v['total_reps']}\n\nJours d’entraînement : {v['active_days']}\n"
        f"Entrées : {v['entries']}"
    )
    if v['best_day'] is not None and v['best_day_reps'] is not None:
        value += f"\n\nMeilleur jour :\n{v['best_day']} — {v['best_day_reps']}"
    return value


def history_days(name: str, *, has_entries: bool) -> str:
    return f"📜 {name}\n\n{'Choisissez un jour :' if has_entries else 'Aucune entrée pour le moment.'}"


def history_day(name: str, performed_on: str, total_reps: str) -> str:
    return f"🏋️ {name}\n{performed_on}\nTotal du jour : {total_reps}"


def history_entry(name: str, performed_on: str, reps: str, total_reps: str) -> str:
    return f"🏋️ {name}\n\n{performed_on}\n{reps}\nTotal : {total_reps}"


def delete_confirmation(performed_on: str, reps: str) -> str:
    return f"Supprimer cette entrée ?\n\n{performed_on}\n{reps}"


def clear_history_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f"Effacer tout l’historique de {name} ?\n\n{entries} entrées\n{total_reps} répétitions\n\nCette action est irréversible."


def clear_history_not_needed(name: str) -> str:
    return f"ℹ️ {name} n’a déjà aucune entrée à effacer."


def history_cleared(name: str, entries: str, total_reps: str) -> str:
    return f"✅ Historique de {name} effacé\n\nEntrées supprimées : {entries}\nRépétitions supprimées : {total_reps}"


def exercise_permanently_deleted(name: str) -> str:
    return f"✅ {name} a été supprimé définitivement"


def hard_delete_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f"Supprimer {name} définitivement ?\n\n{entries} entrées\n{total_reps} répétitions\n\nL’exercice et tout son historique seront supprimés définitivement."


def result_saved(name: str, reps: str, total_reps: int, performed_on: str) -> str:
    return f"✅ Ajouté\n\n{name}\n{reps}\n\nTotal : {total_reps}\nDate : {performed_on}"


def result_input(name: str, performed_on: str) -> str:
    return f"🏋️ {name}\n\nDate : {performed_on}\n\nSaisissez un résultat :\n10\n4x10\n10 9 8 7"


def result_constructor(name: str, performed_on: str, sets: str) -> str:
    return f"🏋️ {name}\n\nDate : {performed_on}\n\nSéries :\n{sets}"


def history_constructor(name: str, sets: str) -> str:
    return f"✏️ {name}\n\nSéries :\n{sets}"


def settings(timezone: str, language_name: str) -> str:
    return f"⚙️ Paramètres\n\nFuseau horaire :\n{timezone}\n\nLangue :\n{language_name}"


CHOOSE_TIMEZONE = "🌍 Fuseau horaire\n\nChoisissez un fuseau horaire :"
ENTER_TIMEZONE = "Saisissez un fuseau horaire IANA, par exemple :\n\nAsia/Tokyo\nEurope/Berlin\nAmerica/Chicago"
ENTER_TIMEZONE_REQUIRED = "Saisissez un fuseau horaire IANA puis réessayez."
INVALID_TIMEZONE = "Fuseau horaire non reconnu. Saisissez un fuseau horaire IANA puis réessayez."
TIMEZONE_CHANGED = "Fuseau horaire modifié"
IMPORT_SEND_FILE = "📥 <b>Importer des données</b>\n\nEnvoyez un fichier JSON contenant des exercices et des entraînements.\n\nLe fichier doit être encodé en UTF-8 et ne pas dépasser 1 Mo."
IMPORT_JSON_ONLY = "Seuls les fichiers .json sont pris en charge."
IMPORT_FILE_TOO_LARGE = "Le fichier est trop volumineux. Taille maximale : 1 Mo."
IMPORT_INVALID_FILE = "Le fichier JSON est invalide ou ne correspond pas au format d’importation."
IMPORT_CANCELLED = "Importation annulée"
EXPORT_NO_EXERCISES = "📤 Exporter des données\n\nAucun exercice à exporter pour le moment."
EXPORT_FILE_TOO_LARGE = "Le fichier dépasse 1 Mo et ne peut pas être importé. Choisissez moins d’exercices."


def export_selection(*, selected: int, total: int) -> str:
    value = f"📤 Exporter des données\n\nChoisissez les exercices à exporter.\n\nLe fichier contiendra toutes les entrées des exercices sélectionnés.\nVous pourrez le réimporter plus tard.\n\nSélectionnés : {selected} sur {total}"
    return value if selected else value + "\n\nChoisissez au moins un exercice."


def export_completed(*, exercises: str, entries: str) -> str:
    return f"✅ Exportation prête\n\nExercices : {exercises}\nEntrées d’entraînement : {entries}"


def import_preview(*, exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str, existing_names: list[str]) -> str:
    value = f"📥 Importer\n\nExercices : {exercises}\nEntrées d’entraînement : {entries}\nTotal de répétitions : {total_reps}\nPériode : {date_from} — {date_to}\n\nNouveaux exercices : {new_count}\nExercices existants : {len(existing_names)}"
    if existing_names:
        value += "\n\nExistants :\n" + "\n".join(f"• {name}" for name in existing_names) + "\n\nComment traiter l’historique existant ?"
    return value


def import_new_exercises_confirmation(*, exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str) -> str:
    return f"📥 Importer\n\nExercices : {exercises}\nEntrées d’entraînement : {entries}\nTotal de répétitions : {total_reps}\nPériode : {date_from} — {date_to}\n\nNouveaux exercices à créer : {new_count}"


def import_confirmation(strategy: str, entries: str, existing_count: int) -> str:
    if strategy == "replace":
        return f"Remplacer l’historique existant ?\n\nL’historique de {existing_count} exercices correspondants sera définitivement supprimé.\n{entries} entrées importées seront ensuite ajoutées."
    return f"Fusionner les données importées ?\n\nLes entrées existantes resteront intactes.\n{entries} nouvelles entrées seront ajoutées.\n\nUne importation répétée peut créer des doublons."


def import_completed(*, strategy: str, created: str, updated: str, entries: str, total_reps: str, include_strategy: bool = True) -> str:
    value = "✅ Importation terminée\n\n"
    if include_strategy:
        value += f"Stratégie : {'Remplacer' if strategy == 'replace' else 'Fusionner'}\n\n"
    return value + f"Exercices créés : {created}\nExercices existants mis à jour : {updated}\nEntrées importées : {entries}\nTotal de répétitions importées : {total_reps}"


def timezone_changed(timezone: str) -> str:
    return f"✅ Fuseau horaire modifié\n\n{timezone}"


def language_changed(language_name: str) -> str:
    return f"✅ Langue modifiée\n\n{language_name}"


def weekly_report_toggle(enabled: bool) -> str:
    return "📅 Rapport hebdomadaire : activé" if enabled else "📅 Rapport hebdomadaire : désactivé"


def weekly_report_changed(enabled: bool) -> str:
    return "Rapport hebdomadaire activé" if enabled else "Rapport hebdomadaire désactivé"


WEEKLY_NO_DATA = "Cet exercice ne contient encore aucune donnée pour une semaine complète."
WEEKLY_CARD_FAILED = "Impossible d’envoyer une des cartes. Réessayez depuis le menu de l’exercice."
WEEKLY_LABELS = dict(title="📅 Rapport hebdomadaire", period="Période", total="Cette semaine : {total} {unit}", first="Aucune semaine complète précédente.", previous="Semaine précédente", change="Évolution", active="Jours actifs", best="Meilleur jour")


def weekly_reps_unit(total: int) -> str:
    return "répétition" if total == 1 else "répétitions"


RESTORE_INPUT_FAILED = "Impossible de restaurer la saisie. Rouvrez l’exercice."
RESTORE_ENTRY_FAILED = "Impossible de restaurer l’entrée."
POSITIVE_RESULT_REQUIRED = "Le nombre de séries et de répétitions doit être positif."
NUMBER_TOO_LARGE = "Le nombre est trop grand."
ENTER_DATE_REQUIRED = "Saisissez une date."
FUTURE_DATE = "Une date future ne peut pas être sélectionnée."
SET_NOT_FOUND = "Série introuvable."
LAST_SET_REQUIRED = "Au moins une série doit rester."
