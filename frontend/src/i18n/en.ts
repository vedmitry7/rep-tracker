/**
 * English UI dictionary for the Repka web app, the reference for every locale.
 *
 * All supported languages (en, ru, es, pt, tr, uk, id, hi, kk, pl, fr) live in
 * sibling files with the same key structure; `index.ts` picks the dictionary
 * from `settings.language`. English is also the fallback for an unknown locale,
 * a missing key, or a missing plural category.
 *
 * Conventions:
 * - `{name}` placeholders are filled via `t(key, { name })`. Placeholder
 *   names stay stable across languages; only the surrounding text translates.
 * - `{count}` marks a plural entry. Plural entries are objects with CLDR
 *   categories (`zero`, `one`, `two`, `few`, `many`, `other`; `other` is
 *   required). Each language defines the categories its `Intl.PluralRules`
 *   needs; `npm run i18n:check` verifies this.
 * - Proper names ("Repka"), IANA timezone IDs, language autonyms
 *   ("Русский", ...), routes, CSS classes and API contracts are NOT here.
 */
export const en = {
  app: {
    brand: "Repka",
    title: "Repka · Workout Tracker",
  },
  common: {
    loading: "Loading your training…",
    loadingShort: "Loading…",
    tryAgain: "Try again",
    saving: "Saving…",
    today: "Today",
    reps: "reps",
    noResultsYet: "No results yet",
    goBack: "Go back",
  },
  connection: {
    eyebrow: "CONNECTION ISSUE",
    title: "Couldn’t reach Repka",
    copy: "Check your connection or VPN, then try again.",
  },
  errors: {
    loadFailed: "Unable to load data. Please try again.",
    requestTimedOut: "The connection timed out. Please try again.",
    openInTelegram: "Open Repka from the Telegram app.",
    exerciseNotFound: "Exercise not found.",
    loadExercises: "Could not load exercises.",
    loadExercise: "Could not load the exercise.",
    loadRecentResults: "Could not load recent results.",
    loadFullHistory: "Could not load the full history.",
    loadWeeklyHistory: "Could not load weekly history.",
    loadResults: "Could not load results.",
    loadMoreDays: "Could not load more days.",
    loadDayResults: "Could not load results for this day.",
    createExercise: "Could not create exercise.",
    saveResult: "Could not save result.",
    deleteResult: "Could not delete result.",
    loadResult: "Could not load result.",
    resultNotFound: "Result not found.",
    invalidResult: "Invalid result format.",
    loadSettings: "Could not load settings.",
    saveSettings: "Could not save settings.",
    saveName: "Could not save the name.",
    updateReport: "Could not update report setting.",
    archiveExercise: "Could not archive the exercise.",
  },
  home: {
    exercisesLabel: "Exercises",
    settingsLabel: "Global settings",
    newExercise: "New exercise",
    openExercise: "Open {name}",
    addResultFor: "Add result for {name}",
    activityLabel: "Last seven days activity",
    emptyTitle: "Your list is ready",
    emptyCopy: "Add the first exercise you want to track.",
    emptyCta: "Add your first exercise",
  },
  newExercise: {
    title: "New exercise",
    nameLabel: "Exercise name",
    create: "Create exercise",
    creating: "Creating…",
  },
  exercise: {
    fallbackTitle: "Exercise",
    settingsLabel: "Exercise settings",
    latest: "Latest",
    addResult: "+ Add result",
    recentTitle: "Recent results",
    recentEmpty: "No results yet. Log your first set.",
    allResults: "All results →",
    loadingResults: "Loading results…",
  },
  progress: {
    title: "Progress",
    periodAll: "All",
    loadingHistory: "Loading full history…",
    barLabel: "{detail}: {total} reps",
    selectedTotal: "{total} reps",
  },
  weekly: {
    title: "Weekly progress",
    allWeeks: "All weeks →",
    empty: "Your weekly progress will appear after the first result.",
    vsLastWeek: "vs last week",
    best: "Best",
    avg: "Avg",
  },
  weeks: {
    title: "All weeks",
    historyTitle: "Weekly history",
    empty: "No weekly history yet.",
    weeksCount: {
      one: "{count} week",
      other: "{count} weeks",
    },
  },
  results: {
    title: "All results",
    historyTitle: "Training history",
    daysCount: {
      one: "{count} day",
      other: "{count} days",
    },
    resultsCount: {
      one: "{count} result",
      other: "{count} results",
    },
    openResult: "Open result: {sets}, {total} reps",
    loadMore: "Load more",
    empty: "No results yet.",
  },
  entry: {
    addTitle: "Add result",
    editTitle: "Edit result",
    quickLabel: "Quick entry",
    quickPlaceholder: "4×10 or 10 + 10 + 8",
    quickHint: "Try 4×10, 10 10 10, or 10 + 10 + 8.",
    emptySetsError: "Enter at least one set.",
    formatError: "Use formats such as 4×10, 10 10 10, or 10 + 10 + 8.",
    rangeError: "Use 1–100 sets with 1–10,000 repetitions each.",
    setsTitle: "Sets",
    setsTotal: "{total} reps total",
    setLabel: "Set {index}",
    decreaseSet: "Decrease set {index}",
    repsForSet: "Repetitions for set {index}",
    increaseSet: "Increase set {index}",
    removeSet: "Remove set {index}",
    addSet: "＋ Add set",
    dateLabel: "Date",
    selectedDateHint: "Selected training date",
    save: "Save result",
    saveChanges: "Save changes",
    delete: "Delete result",
    deleteConfirm: "Delete this result? This cannot be undone.",
  },
  exerciseSettings: {
    title: "Exercise settings",
    nameLabel: "Exercise name",
    saveName: "Save name",
    weeklyTitle: "Weekly report",
    weeklyCopy: "Include this exercise in the weekly summary.",
    weeklyToggle: "Toggle weekly report",
    dangerTitle: "Danger zone",
    dangerCopy: "Archiving hides this exercise from your list. You can restore it later from the bot.",
    archive: "Archive exercise",
    archiveConfirm: "Archive this exercise? Its results will stay saved.",
  },
  settings: {
    title: "Settings",
    eyebrow: "PREFERENCES",
    timezoneLabel: "Time zone",
    timezoneHint: "Uses the same curated timezone choices as the Telegram bot.",
    languageLabel: "Language",
    save: "Save settings",
    verifiedNote: "Your Telegram account is verified securely.",
  },
  time: {
    justNow: "just now",
    minutesAgo: "{count}m ago",
    hoursAgo: "{count}h ago",
    yesterday: "yesterday",
    daysAgo: "{count}d ago",
    moment: "{date}, {time}",
  },
} as const;
