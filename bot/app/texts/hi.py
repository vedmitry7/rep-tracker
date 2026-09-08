"""Hindi Telegram UI copy."""
from .en import *
LANGUAGE_CODE = "hi"
LANGUAGE_NAME = "Hindi"
LANGUAGE_BUTTON = "🇮🇳 Hindi"
EXERCISES_TITLE = "🏋️ Repka\n\nएक व्यायाम चुनें"
NO_EXERCISES = "🏋️ Repka\n\nअभी कोई व्यायाम नहीं है"
BUTTON_SETTINGS = "⚙️ सेटिंग्स"
BUTTON_ADD_EXERCISE = "➕ व्यायाम जोड़ें"
BUTTON_ADD_FIRST_EXERCISE = "➕ अपना पहला व्यायाम जोड़ें"
BUTTON_ADD_RESULT = "➕ परिणाम जोड़ें"
BUTTON_STATISTICS = "📊 आँकड़े"
BUTTON_HISTORY = "📜 इतिहास"
BUTTON_BACK = BUTTON_BACK_ARROW = "← वापस"
BUTTON_CHANGE_LANGUAGE = "🌐 भाषा"
BUTTON_CHANGE_TIMEZONE = "🌍 समय क्षेत्र"
CHOOSE_LANGUAGE = "🌐 भाषा चुनें"
LANGUAGE_CHANGED = "भाषा बदल दी गई"
TODAY, YESTERDAY, DAY_BEFORE_YESTERDAY = "आज", "कल", "परसों"
ENTER_RESULT = "एक परिणाम दर्ज करें।"
INVALID_RESULT_FORMAT = "प्रारूप पहचाना नहीं गया। उदाहरण: 10, 4x10, या 10 9 8।"
INVALID_DATE = "तारीख पहचानी नहीं गई। 25.08, 25.08.2026 या 2026-08-25 का उपयोग करें।"
BACKEND_UNAVAILABLE = "सेवा अस्थायी रूप से उपलब्ध नहीं है। बाद में फिर कोशिश करें।"
BOT_NAME = "Repka · वर्कआउट ट्रैकर"
BOT_SHORT_DESCRIPTION = "व्यायाम दर्ज करें, अपनी प्रगति देखें और साप्ताहिक रिपोर्ट पाएं।"
BOT_DESCRIPTION = "🥬 Repka, Telegram में व्यायाम ट्रैकर है।\n\nसेट और रेप्स एक पंक्ति में दर्ज करें, प्रगति देखें और साप्ताहिक रिपोर्ट पाएं।"
BOT_COMMANDS = {"menu": "मेनू", "settings": "सेटिंग्स", "help": "मदद"}
WELCOME = "🥬 नमस्ते! मैं Repka हूँ।\n\nमैं आपके वर्कआउट सहेजता हूँ और साधारण संख्याओं को आपकी प्रगति की साफ़ कहानी में बदलता हूँ।\n\nएक व्यायाम जोड़ें और 16, 4×10 या 12, 10, 8 जैसा परिणाम भेजें।"
HELP = "ℹ️ मदद\n\nपरिणाम जोड़ने, आँकड़े देखने या इतिहास खोलने के लिए एक व्यायाम चुनें।\n\n/menu — व्यायाम\n/settings — सेटिंग्स"
from ._translations import _apply_button_translations
_apply_button_translations(globals(), LANGUAGE_CODE)

# Dynamic screens and notifications.  Do not inherit these from en.py: every
# message sent to a Hindi user must come from this catalog.
EXERCISE_NOT_FOUND = "व्यायाम नहीं मिला।"
REQUEST_EXERCISE_NAME = "व्यायाम का नाम लिखें"
EMPTY_EXERCISE_NAME = "नाम खाली नहीं हो सकता। फिर से कोशिश करें:"
SCREEN_EXPIRED = "यह स्क्रीन समाप्त हो गई है।"
INPUT_FINISHED = "इनपुट पहले ही पूरा हो चुका है।"
EDIT_FINISHED = "संपादन पहले ही पूरा हो चुका है।"
INPUT_CANCELLED = "रद्द किया गया"
ENTRY_NOT_FOUND = "रिकॉर्ड नहीं मिला।"
DAY_OR_EXERCISE_NOT_FOUND = "दिन या व्यायाम नहीं मिला।"
RESTORE_INPUT_FAILED = "इनपुट बहाल नहीं किया जा सका। व्यायाम फिर से खोलें।"
RESTORE_ENTRY_FAILED = "रिकॉर्ड बहाल नहीं किया जा सका।"
CHOOSE_DATE = "तारीख चुनें:"
CHOOSE_NEW_DATE = "नई तारीख चुनें:"
ENTER_DATE = "तारीख लिखें:\n\n25.08\n25.08.2026\n2026-08-25"
MIN_REPETITIONS = "न्यूनतम 1 है।"
MAX_REPETITIONS = "अधिकतम 10,000 है।"
CHANGES_SAVED = "बदलाव सहेजे गए"
ENTRY_DELETED = "रिकॉर्ड हटाया गया"
DATE_CHANGED = "तारीख बदली गई"
RESULT_ADDED = "जोड़ा गया"
HISTORY_CLEARED = "इतिहास साफ़ किया गया"
ACCESS_FORBIDDEN = "बॉट तक पहुँच प्रतिबंधित है।"
RESOURCE_NOT_FOUND = "डेटा नहीं मिला। /start भेजें और फिर कोशिश करें।"
RESOURCE_CONFLICT = "यह व्यायाम अब उपलब्ध नहीं है।"
DUPLICATE_EXERCISE_NAME = "इस नाम का व्यायाम पहले से मौजूद है।"
REQUEST_FAILED = "अनुरोध पूरा नहीं हो सका। बाद में फिर कोशिश करें।"
POSITIVE_RESULT_REQUIRED = "सेट और दोहराव की संख्या सकारात्मक होनी चाहिए।"
NUMBER_TOO_LARGE = "संख्या बहुत बड़ी है।"
ENTER_DATE_REQUIRED = "तारीख लिखें।"
FUTURE_DATE = "भविष्य की तारीख नहीं चुनी जा सकती।"
SET_NOT_FOUND = "सेट नहीं मिला।"
LAST_SET_REQUIRED = "कम-से-कम एक सेट रहना चाहिए।"


def exercise_name_too_long(max_length: int) -> str:
    return f"नाम बहुत लंबा है। अधिकतम: {max_length} अक्षर।"


def sets_count_out_of_range(max_sets: int) -> str:
    return f"सेट की संख्या 1 से {max_sets} के बीच होनी चाहिए।"


def repetitions_out_of_range(max_repetitions: int) -> str:
    return f"हर सेट में दोहराव 1 से {max_repetitions:,} के बीच होना चाहिए।"


def too_many_sets(max_sets: int) -> str:
    return f"आप {max_sets} से ज़्यादा सेट नहीं जोड़ सकते।"


def exercise_empty(name: str) -> str:
    return f"🏋️ {name}\n\n↩️ पिछला: —\n\n🔥 आज — 0\n📅 7 दिन — 0\n🗓 30 दिन — 0\n🏆 कुल — 0"


def exercise_summary(*, name: str, last_reps: str, last_date: str, today_reps: str,
                     last_7_days_reps: str, last_30_days_reps: str, total_reps: str) -> str:
    return (f"🏋️ {name}\n\n↩️ पिछला: {last_reps} · {last_date.lower()}\n\n"
            f"🔥 आज — {today_reps}\n📅 7 दिन — {last_7_days_reps}\n"
            f"🗓 30 दिन — {last_30_days_reps}\n🏆 कुल — {total_reps}")


EXERCISE_MANAGEMENT = "🛠 व्यायाम प्रबंधित करें"
CLEAR_HISTORY_CHOOSE_EXERCISE = "🧹 इतिहास साफ़ करें\n\nएक व्यायाम चुनें"
DELETE_EXERCISE_CHOOSE_EXERCISE = "🗑 व्यायाम हटाएँ\n\nएक व्यायाम चुनें"


def statistics(*, name: str, today_reps: str, last_7_days_reps: str,
               last_30_days_reps: str, total_reps: str, active_days: str,
               entries: str, best_day: str | None, best_day_reps: str | None) -> str:
    value = (f"📊 {name}\n\nआज: {today_reps}\n7 दिन: {last_7_days_reps}\n"
             f"30 दिन: {last_30_days_reps}\nकुल: {total_reps}\n\n"
             f"प्रशिक्षण के दिन: {active_days}\nरिकॉर्ड: {entries}")
    if best_day is not None and best_day_reps is not None:
        value += f"\n\nसबसे अच्छा दिन:\n{best_day} — {best_day_reps}"
    return value


def history_days(name: str, *, has_entries: bool) -> str:
    return f"📜 {name}\n\n{'एक दिन चुनें:' if has_entries else 'अभी कोई रिकॉर्ड नहीं है।'}"


def history_day(name: str, performed_on: str, total_reps: str) -> str:
    return f"🏋️ {name}\n{performed_on}\nदिन का कुल: {total_reps}"


def history_entry(name: str, performed_on: str, reps: str, total_reps: str) -> str:
    return f"🏋️ {name}\n\n{performed_on}\n{reps}\nकुल: {total_reps}"


def delete_confirmation(performed_on: str, reps: str) -> str:
    return f"इस रिकॉर्ड को हटाएँ?\n\n{performed_on}\n{reps}"


def clear_history_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f"{name} का पूरा इतिहास साफ़ करें?\n\nरिकॉर्ड: {entries}\nदोहराव: {total_reps}\n\nइसे वापस नहीं किया जा सकता।"


def clear_history_not_needed(name: str) -> str:
    return f"ℹ️ {name} में साफ़ करने के लिए कोई रिकॉर्ड नहीं है।"


def history_cleared(name: str, entries: str, total_reps: str) -> str:
    return f"✅ {name} का इतिहास साफ़ किया गया\n\nहटाए गए रिकॉर्ड: {entries}\nहटाए गए दोहराव: {total_reps}"


def exercise_permanently_deleted(name: str) -> str:
    return f"✅ {name} को स्थायी रूप से हटा दिया गया"


def hard_delete_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f"{name} को स्थायी रूप से हटाएँ?\n\nरिकॉर्ड: {entries}\nदोहराव: {total_reps}\n\nव्यायाम और इसका सारा इतिहास स्थायी रूप से हटा दिया जाएगा।"


def result_saved(name: str, reps: str, total_reps: int, performed_on: str) -> str:
    return f"✅ जोड़ा गया\n\n{name}\n{reps}\n\nकुल: {total_reps}\nतारीख: {performed_on}"


def result_input(name: str, performed_on: str) -> str:
    return f"🏋️ {name}\n\nतारीख: {performed_on}\n\nएक परिणाम दर्ज करें:\n10\n4x10\n10 9 8 7"


def result_constructor(name: str, performed_on: str, sets: str) -> str:
    return f"🏋️ {name}\n\nतारीख: {performed_on}\n\nसेट:\n{sets}"


def history_constructor(name: str, sets: str) -> str:
    return f"✏️ {name}\n\nसेट:\n{sets}"


def settings(timezone: str, language_name: str) -> str:
    return f"⚙️ सेटिंग्स\n\nसमय क्षेत्र:\n{timezone}\n\nभाषा:\n{language_name}"


CHOOSE_TIMEZONE = "🌍 समय क्षेत्र\n\nएक समय क्षेत्र चुनें:"
ENTER_TIMEZONE = "IANA समय क्षेत्र लिखें, उदाहरण के लिए:\n\nAsia/Tokyo\nEurope/Berlin\nAmerica/Chicago"
ENTER_TIMEZONE_REQUIRED = "IANA समय क्षेत्र लिखें और फिर कोशिश करें।"
INVALID_TIMEZONE = "समय क्षेत्र पहचाना नहीं गया। IANA समय क्षेत्र लिखें और फिर कोशिश करें।"
TIMEZONE_CHANGED = "समय क्षेत्र बदला गया"
IMPORT_SEND_FILE = "📥 <b>डेटा आयात करें</b>\n\nव्यायाम और वर्कआउट वाली JSON फ़ाइल अपलोड करें।\n\nफ़ाइल UTF-8 एन्कोडिंग में और 1 MB से बड़ी नहीं होनी चाहिए।"
IMPORT_JSON_ONLY = "केवल .json फ़ाइलें समर्थित हैं।"
IMPORT_FILE_TOO_LARGE = "फ़ाइल बहुत बड़ी है। अधिकतम आकार 1 MB है।"
IMPORT_INVALID_FILE = "JSON फ़ाइल अमान्य है या आयात प्रारूप से मेल नहीं खाती।"
IMPORT_CANCELLED = "आयात रद्द किया गया"


def export_selection(*, selected: int, total: int) -> str:
    value = f"📤 डेटा निर्यात करें\n\nनिर्यात के लिए व्यायाम चुनें।\n\nचुना गया: {selected} में से {total}"
    return value if selected else value + "\n\nकम-से-कम एक व्यायाम चुनें।"


EXPORT_NO_EXERCISES = "📤 डेटा निर्यात करें\n\nनिर्यात करने के लिए अभी कोई व्यायाम नहीं है।"
EXPORT_FILE_TOO_LARGE = "फ़ाइल 1 MB से बड़ी है और आयात नहीं की जा सकती। कम व्यायाम चुनें।"


def export_completed(*, exercises: str, entries: str) -> str:
    return f"✅ निर्यात तैयार है\n\nव्यायाम: {exercises}\nवर्कआउट रिकॉर्ड: {entries}"


def import_preview(*, exercises: str, entries: str, total_reps: str, date_from: str,
                   date_to: str, new_count: str, existing_names: list[str]) -> str:
    value = (f"📥 आयात\n\nव्यायाम: {exercises}\nवर्कआउट रिकॉर्ड: {entries}\nकुल दोहराव: {total_reps}\n"
             f"तारीख सीमा: {date_from} — {date_to}\n\nनए व्यायाम: {new_count}\nमौजूदा व्यायाम: {len(existing_names)}")
    if existing_names:
        value += "\n\nमौजूदा:\n" + "\n".join(f"• {name}" for name in existing_names)
        value += "\n\nमौजूदा इतिहास को कैसे संभालना है?"
    return value


def import_new_exercises_confirmation(*, exercises: str, entries: str, total_reps: str,
                                      date_from: str, date_to: str, new_count: str) -> str:
    return (f"📥 आयात\n\nव्यायाम: {exercises}\nवर्कआउट रिकॉर्ड: {entries}\nकुल दोहराव: {total_reps}\n"
            f"तारीख सीमा: {date_from} — {date_to}\n\nबनाए जाने वाले नए व्यायाम: {new_count}")


def import_confirmation(strategy: str, entries: str, existing_count: int) -> str:
    if strategy == "replace":
        return f"मौजूदा इतिहास बदलें?\n\n{existing_count} मिलते-जुलते व्यायामों का इतिहास स्थायी रूप से हटाया जाएगा।\nफिर {entries} आयात किए गए रिकॉर्ड जोड़े जाएँगे।"
    return f"आयात किया गया डेटा मिलाएँ?\n\nमौजूदा रिकॉर्ड रहेंगे।\n{entries} नए रिकॉर्ड जोड़े जाएँगे।\n\nबार-बार आयात करने से डुप्लिकेट बन सकते हैं।"


def import_completed(*, strategy: str, created: str, updated: str, entries: str,
                     total_reps: str, include_strategy: bool = True) -> str:
    value = "✅ आयात पूरा हुआ\n\n"
    if include_strategy:
        value += f"रणनीति: {'बदलें' if strategy == 'replace' else 'मिलाएँ'}\n\n"
    return value + f"बनाए गए व्यायाम: {created}\nअपडेट किए गए मौजूदा व्यायाम: {updated}\nआयात किए गए रिकॉर्ड: {entries}\nआयात किए गए कुल दोहराव: {total_reps}"


def timezone_changed(timezone: str) -> str:
    return f"✅ समय क्षेत्र बदला गया\n\n{timezone}"


def language_changed(language_name: str) -> str:
    return f"✅ भाषा बदली गई\n\n{language_name}"


def weekly_report_toggle(enabled: bool) -> str:
    return "📅 साप्ताहिक रिपोर्ट: चालू" if enabled else "📅 साप्ताहिक रिपोर्ट: बंद"


def weekly_report_changed(enabled: bool) -> str:
    return "साप्ताहिक रिपोर्ट चालू की गई" if enabled else "साप्ताहिक रिपोर्ट बंद की गई"


WEEKLY_NO_DATA = "इस व्यायाम के लिए अभी किसी पूर्ण सप्ताह का डेटा नहीं है।"
WEEKLY_CARD_FAILED = "कार्ड में से एक भेजा नहीं जा सका। व्यायाम मेनू से फिर कोशिश करें।"
WEEKLY_LABELS = dict(title="📅 साप्ताहिक रिपोर्ट", period="अवधि", total="इस सप्ताह: {total} {unit}", first="पिछला पूर्ण सप्ताह अभी नहीं है।", previous="पिछला सप्ताह", change="बदलाव", active="सक्रिय दिन", best="सबसे अच्छा दिन")


def weekly_reps_unit(total: int) -> str:
    return "दोहराव" if total == 1 else "दोहराव"
