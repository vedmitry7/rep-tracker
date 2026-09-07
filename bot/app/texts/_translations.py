"""Shared, complete labels for the language-neutral Telegram controls."""

_BUTTON_KEYS = (
    "BUTTON_EXERCISES", "BUTTON_CONSTRUCTOR", "BUTTON_CHANGE_DATE", "BUTTON_DATE",
    "BUTTON_ENTER_DATE", "BUTTON_CANCEL", "BUTTON_CANCEL_PLAIN", "BUTTON_REMOVE_SET",
    "BUTTON_ADD_SET", "BUTTON_ADD", "BUTTON_SAVE", "BUTTON_EDIT", "BUTTON_DELETE",
    "BUTTON_CLEAR_HISTORY", "BUTTON_DELETE_EXERCISE", "BUTTON_CONFIRM_CLEAR_HISTORY",
    "BUTTON_DELETE_PERMANENTLY", "BUTTON_CONFIRM_DELETE", "BUTTON_OTHER_TIMEZONE",
    "BUTTON_PREVIOUS", "BUTTON_NEXT", "BUTTON_IMPORT_DATA", "BUTTON_EXPORT_DATA",
    "BUTTON_EXERCISE_MANAGEMENT", "BUTTON_IMPORT_MERGE", "BUTTON_IMPORT_REPLACE",
    "BUTTON_IMPORT", "BUTTON_REPLACE_AND_IMPORT", "BUTTON_EXPORT", "BUTTON_GENERATE_CARDS",
    "BUTTON_WEEKLY_CARD",
)

_BUTTONS = {
    "es": ("← Ejercicios", "🎛 Constructor", "📅 Cambiar fecha", "📅 Fecha", "✏️ Introducir fecha", "❌ Cancelar", "Cancelar", "➖ Serie", "➕ Serie", "✅ Añadir", "✅ Guardar", "✏️ Editar", "🗑 Eliminar", "🧹 Borrar historial", "🗑 Eliminar ejercicio", "🧹 Borrar historial", "🗑 Eliminar permanentemente", "🔴 Sí, eliminar", "🌍 Otra zona horaria", "◀️ Anterior", "Siguiente ▶️", "📥 Importar datos", "📤 Exportar datos", "🛠 Gestionar ejercicios", "🔀 Combinar", "♻️ Reemplazar", "Importar", "Reemplazar e importar", "📤 Exportar", "🖼 Generar tarjetas", "🖼 Tarjeta semanal"),
    "pt": ("← Exercícios", "🎛 Construtor", "📅 Alterar data", "📅 Data", "✏️ Inserir data", "❌ Cancelar", "Cancelar", "➖ Série", "➕ Série", "✅ Adicionar", "✅ Salvar", "✏️ Editar", "🗑 Excluir", "🧹 Limpar histórico", "🗑 Excluir exercício", "🧹 Limpar histórico", "🗑 Excluir permanentemente", "🔴 Sim, excluir", "🌍 Outro fuso horário", "◀️ Anterior", "Próximo ▶️", "📥 Importar dados", "📤 Exportar dados", "🛠 Gerenciar exercícios", "🔀 Mesclar", "♻️ Substituir", "Importar", "Substituir e importar", "📤 Exportar", "🖼 Gerar cartões", "🖼 Cartão semanal"),
    "tr": ("← Egzersizler", "🎛 Oluşturucu", "📅 Tarihi değiştir", "📅 Tarih", "✏️ Tarih gir", "❌ İptal", "İptal", "➖ Set", "➕ Set", "✅ Ekle", "✅ Kaydet", "✏️ Düzenle", "🗑 Sil", "🧹 Geçmişi temizle", "🗑 Egzersizi sil", "🧹 Geçmişi temizle", "🗑 Kalıcı olarak sil", "🔴 Evet, sil", "🌍 Diğer saat dilimi", "◀️ Önceki", "Sonraki ▶️", "📥 Veri içe aktar", "📤 Veri dışa aktar", "🛠 Egzersizleri yönet", "🔀 Birleştir", "♻️ Değiştir", "İçe aktar", "Değiştir ve içe aktar", "📤 Dışa aktar", "🖼 Kartları oluştur", "🖼 Haftalık kart"),
    "uk": ("← Вправи", "🎛 Конструктор", "📅 Змінити дату", "📅 Дата", "✏️ Ввести дату", "❌ Скасувати", "Скасувати", "➖ Підхід", "➕ Підхід", "✅ Додати", "✅ Зберегти", "✏️ Редагувати", "🗑 Видалити", "🧹 Очистити історію", "🗑 Видалити вправу", "🧹 Очистити історію", "🗑 Видалити назавжди", "🔴 Так, видалити", "🌍 Інший часовий пояс", "◀️ Попередня", "Наступна ▶️", "📥 Імпортувати дані", "📤 Експортувати дані", "🛠 Керувати вправами", "🔀 Об’єднати", "♻️ Замінити", "Імпортувати", "Замінити й імпортувати", "📤 Експортувати", "🖼 Створити картки", "🖼 Тижнева картка"),
    "id": ("← Latihan", "🎛 Penyusun", "📅 Ubah tanggal", "📅 Tanggal", "✏️ Masukkan tanggal", "❌ Batal", "Batal", "➖ Set", "➕ Set", "✅ Tambah", "✅ Simpan", "✏️ Edit", "🗑 Hapus", "🧹 Hapus riwayat", "🗑 Hapus latihan", "🧹 Hapus riwayat", "🗑 Hapus permanen", "🔴 Ya, hapus", "🌍 Zona waktu lain", "◀️ Sebelumnya", "Berikutnya ▶️", "📥 Impor data", "📤 Ekspor data", "🛠 Kelola latihan", "🔀 Gabungkan", "♻️ Ganti", "Impor", "Ganti dan impor", "📤 Ekspor", "🖼 Buat kartu", "🖼 Kartu mingguan"),
    "hi": ("← व्यायाम", "🎛 कंस्ट्रक्टर", "📅 तारीख बदलें", "📅 तारीख", "✏️ तारीख दर्ज करें", "❌ रद्द करें", "रद्द करें", "➖ सेट", "➕ सेट", "✅ जोड़ें", "✅ सहेजें", "✏️ संपादित करें", "🗑 हटाएं", "🧹 इतिहास साफ़ करें", "🗑 व्यायाम हटाएं", "🧹 स्थायी रूप से हटाएं", "🗑 स्थायी रूप से हटाएं", "🔴 हाँ, हटाएं", "🌍 अन्य समय क्षेत्र", "◀️ पिछला", "अगला ▶️", "📥 डेटा आयात करें", "📤 डेटा निर्यात करें", "🛠 व्यायाम प्रबंधित करें", "🔀 मिलाएं", "♻️ बदलें", "आयात करें", "बदलें और आयात करें", "📤 निर्यात करें", "🖼 कार्ड बनाएं", "🖼 साप्ताहिक कार्ड"),
    "kk": ("← Жаттығулар", "🎛 Құрастырғыш", "📅 Күнді өзгерту", "📅 Күн", "✏️ Күнді енгізу", "❌ Болдырмау", "Болдырмау", "➖ Жиын", "➕ Жиын", "✅ Қосу", "✅ Сақтау", "✏️ Өңдеу", "🗑 Жою", "🧹 Тарихты тазалау", "🗑 Жаттығуды жою", "🧹 Тарихты тазалау", "🗑 Біржола жою", "🔴 Иә, жою", "🌍 Басқа уақыт белдеуі", "◀️ Алдыңғы", "Келесі ▶️", "📥 Деректерді импорттау", "📤 Деректерді экспорттау", "🛠 Жаттығуларды басқару", "🔀 Біріктіру", "♻️ Ауыстыру", "Импорттау", "Ауыстыру және импорттау", "📤 Экспорттау", "🖼 Карточкалар жасау", "🖼 Апталық карточка"),
    "pl": ("← Ćwiczenia", "🎛 Konstruktor", "📅 Zmień datę", "📅 Data", "✏️ Wpisz datę", "❌ Anuluj", "Anuluj", "➖ Seria", "➕ Seria", "✅ Dodaj", "✅ Zapisz", "✏️ Edytuj", "🗑 Usuń", "🧹 Wyczyść historię", "🗑 Usuń ćwiczenie", "🧹 Wyczyść historię", "🗑 Usuń trwale", "🔴 Tak, usuń", "🌍 Inna strefa czasowa", "◀️ Poprzednia", "Następna ▶️", "📥 Importuj dane", "📤 Eksportuj dane", "🛠 Zarządzaj ćwiczeniami", "🔀 Scal", "♻️ Zastąp", "Importuj", "Zastąp i importuj", "📤 Eksportuj", "🖼 Generuj karty", "🖼 Karta tygodniowa"),
    "fr": ("← Exercices", "🎛 Constructeur", "📅 Modifier la date", "📅 Date", "✏️ Saisir la date", "❌ Annuler", "Annuler", "➖ Série", "➕ Série", "✅ Ajouter", "✅ Enregistrer", "✏️ Modifier", "🗑 Supprimer", "🧹 Effacer l’historique", "🗑 Supprimer l’exercice", "🧹 Effacer l’historique", "🗑 Supprimer définitivement", "🔴 Oui, supprimer", "🌍 Autre fuseau horaire", "◀️ Précédent", "Suivant ▶️", "📥 Importer des données", "📤 Exporter les données", "🛠 Gérer les exercices", "🔀 Fusionner", "♻️ Remplacer", "Importer", "Remplacer et importer", "📤 Exporter", "🖼 Générer les cartes", "🖼 Carte hebdomadaire"),
}


def _apply_button_translations(namespace: dict[str, object], language: str) -> None:
    namespace.update(zip(_BUTTON_KEYS, _BUTTONS[language], strict=True))
