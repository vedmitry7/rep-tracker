"""Brazilian Portuguese Telegram UI copy."""

"""Cópia da UI do Telegram em inglês."""
LANGUAGE_CODE = 'pt'
LANGUAGE_NAME = 'Português (Brasil)'
LANGUAGE_BUTTON = '🇧🇷 Português (Brasil)'
BOT_NAME = 'Repka · Rastreador de treino'
BOT_COMMANDS = {'menu': 'Cardápio', 'settings': 'Configurações', 'help': 'Ajuda'}
BOT_SHORT_DESCRIPTION = 'Acompanhe os exercícios, veja seu progresso e receba relatórios semanais.'
BOT_DESCRIPTION = '🥬 Repka é um rastreador de exercícios no Telegram.\n\nRegistre séries e repetições em uma linha: 16, 4×10 ou 12, 10, 8. Repka salva o resultado, totaliza suas repetições do dia, semana e mês e mostra o progresso de cada exercício.\n\n📊 Estatísticas e histórico de treinamento\n🖼 Relatórios semanais que valem a pena compartilhar\n📦 Importação e exportação de dados'
EXERCISES_TITLE = '🏋️ Repka\n\nO que vamos treinar hoje?'
NO_EXERCISES = '🏋️Repka\n\nAinda não há exercícios'
WELCOME = '🥬 Olá! Eu sou Repka.\n\nLembro-me dos seus treinos e transformo números simples em uma história clara do seu progresso.\n\nComeçar é fácil:\n1. Adicione um exercício – por exemplo, Flexões.\n2. Após o treino, envie um resultado: 16, 4×10 ou 12, 10, 8.\n3. Vou salvá-lo e calcular suas estatísticas.\n\nCom o tempo, você verá seu histórico de treino, progresso semanal e mensal e relatórios semanais que você pode compartilhar.\n\nSeus dados podem ser importados e exportados – eles nunca são bloqueados dentro do Repka.\n\n👇 Adicione seu primeiro exercício. Leva apenas alguns segundos.'
HELP = 'ℹ️ Ajuda\n\nEscolha um exercício para adicionar um resultado, visualizar estatísticas ou abrir o histórico.\n\n/menu — exercícios\n/settings — configurações'
EXERCISE_NOT_FOUND = 'Exercício não encontrado.'
REQUEST_EXERCISE_NAME = 'Digite o nome do exercício'
EMPTY_EXERCISE_NAME = 'O nome não pode ficar vazio. Tente novamente:'
SCREEN_EXPIRED = 'Esta tela expirou.'
INPUT_FINISHED = 'A entrada já foi concluída.'
EDIT_FINISHED = 'A edição já terminou.'
INPUT_CANCELLED = 'Cancelado'
ENTRY_NOT_FOUND = 'Entrada não encontrada.'
DAY_OR_EXERCISE_NOT_FOUND = 'Dia ou exercício não encontrado.'
RESTORE_INPUT_FAILED = 'Não foi possível restaurar a entrada. Abra o exercício novamente.'
RESTORE_ENTRY_FAILED = 'Não foi possível restaurar a entrada.'
CHOOSE_DATE = 'Escolha uma data:'
CHOOSE_NEW_DATE = 'Escolha uma nova data:'
ENTER_DATE = 'Insira uma data:\n\n25.08\n25.08.2026\n25/08/2026'
TODAY = 'Hoje'
YESTERDAY = 'Ontem'
DAY_BEFORE_YESTERDAY = 'Anteontem'
MIN_REPETITIONS = 'O mínimo é 1.'
MAX_REPETITIONS = 'O máximo é 10.000.'
CHANGES_SAVED = 'Alterações salvas'
ENTRY_DELETED = 'Entrada excluída'
DATE_CHANGED = 'Data alterada'
RESULT_ADDED = 'Adicionado'
HISTORY_CLEARED = 'Histórico apagado'
ACCESS_FORBIDDEN = 'O acesso ao bot é restrito.'
BACKEND_UNAVAILABLE = 'O serviço está temporariamente indisponível. Tente novamente mais tarde.'
RESOURCE_NOT_FOUND = 'Dados não encontrados. Envie /start e tente novamente.'
RESOURCE_CONFLICT = 'O exercício não está mais disponível.'
DUPLICATE_EXERCISE_NAME = 'Já existe um exercício com este nome.'
REQUEST_FAILED = 'Não foi possível concluir a solicitação. Tente novamente mais tarde.'
BUTTON_ADD_EXERCISE = '➕ Adicione exercício'
BUTTON_ADD_FIRST_EXERCISE = '➕ Adicione seu primeiro exercício'
BUTTON_SETTINGS = '⚙️ Configurações'
BUTTON_ADD_RESULT = '➕ Adicionar resultado'
BUTTON_STATISTICS = '📊 Estatísticas'
BUTTON_HISTORY = '📜 História'
BUTTON_EXERCISES = '← Exercícios'
BUTTON_BACK = '← Voltar'
BUTTON_BACK_ARROW = '← Voltar'
BUTTON_CONSTRUCTOR = '🎛 Construtor'
BUTTON_CHANGE_DATE = '📅 Alterar data'
BUTTON_DATE = '📅 Data'
BUTTON_ENTER_DATE = '✏️ Insira a data'
BUTTON_CANCEL = '❌ Cancelar'
BUTTON_CANCEL_PLAIN = 'Cancelar'
BUTTON_REMOVE_SET = '➖ Definir'
BUTTON_ADD_SET = '➕ Definir'
BUTTON_ADD = '✅ Adicionar'
BUTTON_SAVE = '✅ Salvar'
BUTTON_EDIT = '✏️ Editar'
BUTTON_DELETE = '🗑 Excluir'
BUTTON_CLEAR_HISTORY = '🧹 Limpar histórico'
BUTTON_DELETE_EXERCISE = '🗑 Excluir exercício'
BUTTON_CONFIRM_CLEAR_HISTORY = '🧹 Limpar histórico'
BUTTON_DELETE_PERMANENTLY = '🗑 Excluir permanentemente'
BUTTON_CONFIRM_DELETE = '🔴 Sim, exclua'
BUTTON_CHANGE_TIMEZONE = '🌍 Fuso horário'
BUTTON_OTHER_TIMEZONE = '🌍 Outro fuso horário'
BUTTON_PREVIOUS = '◀️ Anterior'
BUTTON_NEXT = 'Próximo ▶️'
BUTTON_CHANGE_LANGUAGE = '🌐 Idioma'
BUTTON_IMPORT_DATA = '📥 Importar dados'
BUTTON_EXPORT_DATA = '📤 Exportar dados'
BUTTON_EXERCISE_MANAGEMENT = '🛠 Gerenciar exercícios'
BUTTON_IMPORT_MERGE = '🔀 Mesclar'
BUTTON_IMPORT_REPLACE = '♻️ Substituir'
BUTTON_IMPORT = 'Importar'
BUTTON_REPLACE_AND_IMPORT = 'Substituir e importar'
BUTTON_EXPORT = '📤 Exportar'
ENTER_RESULT = 'Insira um resultado.'
POSITIVE_RESULT_REQUIRED = 'O número de séries e repetições deve ser positivo.'
INVALID_RESULT_FORMAT = 'Formato não reconhecido. Exemplos: 10, 4x10 ou 10 9 8.'
NUMBER_TOO_LARGE = 'O número é muito grande.'
ENTER_DATE_REQUIRED = 'Insira uma data.'
INVALID_DATE = 'Data não reconhecida. Use 25/08, 25/08/2026 ou 25/08/2026.'
FUTURE_DATE = 'Uma data futura não pode ser selecionada.'
SET_NOT_FOUND = 'Conjunto não encontrado.'
LAST_SET_REQUIRED = 'Pelo menos um conjunto deve permanecer.'

def exercise_name_too_long(max_length: int) -> str:
    return f'O nome é muito longo. Máximo: {max_length} personagens.'

def sets_count_out_of_range(max_sets: int) -> str:
    return f'O número de conjuntos deve estar entre 1 e {max_sets}.'

def repetitions_out_of_range(max_repetitions: int) -> str:
    return f'As repetições em cada série devem ser entre 1 e {max_repetitions:,}.'

def too_many_sets(max_sets: int) -> str:
    return f'Você não pode adicionar mais do que {max_sets} conjuntos.'

def exercise_empty(name: str) -> str:
    return f'🏋️ {name}\n\n↩️ Mais recentes: -\n\n🔥 Hoje — 0\n📅 7 dias — 0\n🗓 30 dias — 0\n🏆 Total — 0'

def exercise_summary(*, name: str, last_reps: str, last_date: str, today_reps: str, last_7_days_reps: str, last_30_days_reps: str, total_reps: str) -> str:
    return f'🏋️ {name}\n\n↩️ Mais recentes: {last_reps} · {last_date.lower()}\n\n🔥 Hoje - {today_reps}\n📅 7 dias — {last_7_days_reps}\n🗓 30 dias — {last_30_days_reps}\n🏆 Total — {total_reps}'
EXERCISE_MANAGEMENT = '🛠 Gerenciar exercícios'
CLEAR_HISTORY_CHOOSE_EXERCISE = '🧹 Limpar histórico\n\nEscolha um exercício'
DELETE_EXERCISE_CHOOSE_EXERCISE = '🗑 Excluir exercício\n\nEscolha um exercício'

def statistics(*, name: str, today_reps: str, last_7_days_reps: str, last_30_days_reps: str, total_reps: str, active_days: str, average_training_day: str, best_day: str | None, best_day_reps: str | None) -> str:
    value = f'📊 {name}\n\nHoje: {today_reps}\n7 dias: {last_7_days_reps}\n30 dias: {last_30_days_reps}\nTodos os tempos: {total_reps}\n\nDias de treinamento: {active_days}\nMédia por dia de treino: {average_training_day}'
    if best_day is not None and best_day_reps is not None:
        value += f'\n\nMelhor dia:\n{best_day} - {best_day_reps}'
    return value

def history_days(name: str, *, has_entries: bool) -> str:
    suffix = 'Escolha um dia:' if has_entries else 'Nenhuma entrada ainda.'
    return f'📜 {name}\n\n{suffix}'

def history_day(name: str, performed_on: str, total_reps: str) -> str:
    return f'🏋️ {name}\n{performed_on}\nTotal do dia: {total_reps}'

def history_entry(name: str, performed_on: str, reps: str, total_reps: str) -> str:
    return f'🏋️ {name}\n\n{performed_on}\n{reps}\nTotal: {total_reps}'

def delete_confirmation(performed_on: str, reps: str) -> str:
    return f'Excluir esta entrada?\n\n{performed_on}\n{reps}'

def clear_history_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f'Limpar todo o histórico de {name}?\n\n{entries} entradas\n{total_reps} repetições\n\nIsto não pode ser desfeito.'

def clear_history_not_needed(name: str) -> str:
    return f'ℹ️{name}já não tem entradas para limpar.'

def history_cleared(name: str, entries: str, total_reps: str) -> str:
    return f'✅ História para {name} limpo\n\nEntradas removidas: {entries}\nRepetições removidas: {total_reps}'

def exercise_permanently_deleted(name: str) -> str:
    return f'✅ {name} foi excluído permanentemente'

def hard_delete_confirmation(name: str, entries: str, total_reps: str) -> str:
    return f'Excluir {name} permanentemente?\n\n{entries} entradas\n{total_reps} repetições\n\nO exercício e todo o seu histórico serão excluídos permanentemente.'

def result_saved(name: str, reps: str, total_reps: int, performed_on: str) -> str:
    return f'✅ Adicionado\n\n{name}\n{reps}\n\nTotal: {total_reps}\nData: {performed_on}'

def result_input(name: str, performed_on: str) -> str:
    return f'🏋️ {name}\n\nData: {performed_on}\n\nInsira um resultado:\n10\n4x10\n10 9 8 7'

def result_constructor(name: str, performed_on: str, sets: str) -> str:
    return f'🏋️ {name}\n\nData: {performed_on}\n\nConjuntos:\n{sets}'

def history_constructor(name: str, sets: str) -> str:
    return f'✏️ {name}\n\nConjuntos:\n{sets}'

def settings(timezone: str, language_name: str) -> str:
    return f'⚙️ Configurações\n\nFuso horário:\n{timezone}\n\nIdioma:\n{language_name}'
CHOOSE_TIMEZONE = '🌍 Fuso horário\n\nEscolha um fuso horário:'
ENTER_TIMEZONE = 'Insira um fuso horário da IANA, por exemplo:\n\nÁsia/Tóquio\nEuropa/Berlim\nAmérica/Chicago'
ENTER_TIMEZONE_REQUIRED = 'Insira um fuso horário da IANA e tente novamente.'
INVALID_TIMEZONE = 'Fuso horário não reconhecido. Insira um fuso horário da IANA e tente novamente.'
TIMEZONE_CHANGED = 'Fuso horário alterado'
CHOOSE_LANGUAGE = '🌐 Escolha um idioma'
LANGUAGE_CHANGED = 'Idioma alterado'
IMPORT_SEND_FILE = '📥 <b>Importar dados</b>\n\nFaça upload de um arquivo JSON com exercícios e treinos.\n\nO arquivo deve usar codificação UTF-8 e não ter mais que 1 MB.'
IMPORT_JSON_ONLY = 'Somente arquivos .json são suportados.'
IMPORT_FILE_TOO_LARGE = 'O arquivo é muito grande. O tamanho máximo é 1 MB.'
IMPORT_INVALID_FILE = 'O arquivo JSON é inválido ou não corresponde ao formato de importação.'
IMPORT_CANCELLED = 'Importação cancelada'

def export_selection(*, selected: int, total: int) -> str:
    value = f'📤 Exportar dados\n\nEscolha exercícios para exportar.\n\nO arquivo incluirá todas as entradas de treino para os exercícios selecionados.\nVocê pode importar o arquivo novamente mais tarde.\n\nSelecionado: {selected} de {total}'
    if selected == 0:
        value += '\n\nEscolha pelo menos um exercício.'
    return value
EXPORT_NO_EXERCISES = '📤 Exportar dados\n\nAinda não há exercícios para exportar.'
EXPORT_FILE_TOO_LARGE = 'O arquivo é maior que 1 MB e não pode ser importado. Escolha menos exercícios.'

def export_completed(*, exercises: str, entries: str) -> str:
    return f'✅ Pronto para exportação\n\nExercícios: {exercises}\nEntradas de treino: {entries}'

def import_preview(*, exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str, existing_names: list[str]) -> str:
    value = f'📥 Importar\n\nExercícios: {exercises}\nEntradas de treino: {entries}\nRepetições totais: {total_reps}\nPeríodo: {date_from} - {date_to}\n\nNovos exercícios: {new_count}\nExercícios existentes: {len(existing_names)}'
    if existing_names:
        value += '\n\nExistente:\n' + '\n'.join((f'•{name}' for name in existing_names))
        value += '\n\nComo o histórico existente deve ser tratado?'
    return value

def import_new_exercises_confirmation(*, exercises: str, entries: str, total_reps: str, date_from: str, date_to: str, new_count: str) -> str:
    return f'📥 Importar\n\nExercícios: {exercises}\nEntradas de treino: {entries}\nRepetições totais: {total_reps}\nPeríodo: {date_from} - {date_to}\n\nNovos exercícios a serem criados: {new_count}'

def import_confirmation(strategy: str, entries: str, existing_count: int) -> str:
    if strategy == 'replace':
        return f'Substituir o histórico existente?\n\nHistória para {existing_count} os exercícios correspondentes serão excluídos permanentemente.\n{entries} entradas importadas serão então adicionadas.'
    return f'Mesclar dados importados?\n\nAs entradas existentes permanecerão.\n{entries} novas entradas serão adicionadas.\n\nA importação repetida pode criar duplicatas.'

def import_completed(*, strategy: str, created: str, updated: str, entries: str, total_reps: str, include_strategy: bool=True) -> str:
    strategy_name = 'Substituir' if strategy == 'replace' else 'Mesclar'
    value = '✅ Importação concluída\n\n'
    if include_strategy:
        value += f'Estratégia: {strategy_name}\n\n'
    return value + f'Exercícios criados: {created}\nExercícios existentes atualizados: {updated}\nEntradas importadas: {entries}\nTotal de representantes importados: {total_reps}'

def timezone_changed(timezone: str) -> str:
    return f'✅ Fuso horário alterado\n\n{timezone}'

def language_changed(language_name: str) -> str:
    return f'✅ Idioma alterado\n\n{language_name}'
BUTTON_GENERATE_CARDS = '🖼 Gerar cartões'
BUTTON_WEEKLY_CARD = '🖼 Cartão semanal'

def weekly_report_toggle(enabled: bool) -> str:
    return '📅 Relatório semanal: em' if enabled else '📅 Relatório semanal: desativado'

def weekly_report_changed(enabled: bool) -> str:
    return 'Relatório semanal ativado' if enabled else 'Relatório semanal desativado'
WEEKLY_NO_DATA = 'Este exercício ainda não possui dados de semanas completas.'
WEEKLY_CARD_FAILED = 'Não foi possível enviar um dos cartões. Tente novamente no menu de exercícios.'
WEEKLY_LABELS = dict(title='📅 Relatório semanal', period='Período', total='Esta semana: {total} {unidade}', first='Nenhuma semana anterior completa ainda.', previous='Semana anterior', change='Mudança', active='Dias ativos', best='Melhor dia')

def weekly_reps_unit(total: int) -> str:
    return 'representante' if total == 1 else 'repetições'
