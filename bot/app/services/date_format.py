"""Localized presentation formats for calendar dates in the Telegram UI."""

from datetime import date

from bot.app.texts import current_language, normalize_language_code


_MONTHS: dict[str, tuple[str, ...]] = {
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
    "es": ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"),
    "fr": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"),
    "hi": ("जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"),
    "id": ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"),
    "kk": ("қаңтар", "ақпан", "наурыз", "сәуір", "мамыр", "маусым", "шілде", "тамыз", "қыркүйек", "қазан", "қараша", "желтоқсан"),
    "pl": ("stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września", "października", "listopada", "grudnia"),
    "pt": ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"),
    "ru": ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"),
    "tr": ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"),
    "uk": ("січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"),
}


def format_user_date(value: date, *, language: str | None = None) -> str:
    """Render a full, readable date for the selected UI language."""
    locale = normalize_language_code(language or current_language())
    month = _MONTHS[locale][value.month - 1]
    if locale == "en":
        return f"{month} {value.day}, {value.year}"
    if locale in {"es", "pt"}:
        return f"{value.day} de {month} de {value.year}"
    if locale == "kk":
        return f"{value.year} жылғы {value.day} {month}"
    if locale == "tr":
        return f"{value.day} {month} {value.year}"
    return f"{value.day} {month} {value.year}"
