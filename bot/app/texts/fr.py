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
