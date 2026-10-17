import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { appDataCache, type ExerciseDetail, type ExerciseSummary } from "./data-cache";
import repkaLogo from "./assets/repka-logo.png";
import type { Exercise, ExerciseEntry, HistoryDay, Settings } from "./types";
import { t } from "./i18n";
import {
  formatDate,
  formatDayNumeric,
  formatMonth,
  formatNumber,
  formatPercentChange,
  formatSets,
  formatTime,
  formatWeekRange,
  formatWeekdayNarrow,
  formatWeekdayShort,
  parseQuickResult,
  relativeEntryTime,
  totalReps,
} from "./i18n/format";

type Route = "home" | "new-exercise" | "exercise" | "new-entry" | "exercise-settings" | "settings" | "weeks" | "results" | "edit-entry";

type AppRoute = { name: Route; exerciseId?: number; entryId?: number; returnToHome?: boolean };
const languageOptions: Array<{ value: Settings["language"]; label: string }> = [
  { value: "en", label: "English" }, { value: "ru", label: "Русский" }, { value: "es", label: "Español" },
  { value: "pt", label: "Português" }, { value: "tr", label: "Türkçe" }, { value: "uk", label: "Українська" },
  { value: "id", label: "Bahasa Indonesia" }, { value: "hi", label: "हिन्दी" }, { value: "kk", label: "Қазақша" },
  { value: "pl", label: "Polski" }, { value: "fr", label: "Français" },
];

// Matches the curated timezone catalogue used by the Telegram bot. Keeping this
// list in the UI makes the common choices quick to select without asking users
// to know an IANA identifier by heart.
const timezoneOptions = [
  ["Etc/GMT+12", "International Date Line West"], ["Pacific/Pago_Pago", "American Samoa"],
  ["Pacific/Honolulu", "Hawaii"], ["Pacific/Marquesas", "Marquesas Islands"],
  ["America/Anchorage", "Alaska"], ["America/Los_Angeles", "Pacific Time"],
  ["America/Denver", "Mountain Time"], ["America/Chicago", "Central Time"],
  ["America/New_York", "Eastern Time"], ["America/Halifax", "Atlantic Time"],
  ["America/St_Johns", "Newfoundland"], ["America/Sao_Paulo", "São Paulo, Brasília"],
  ["Atlantic/South_Georgia", "South Georgia"], ["Atlantic/Azores", "Azores"],
  ["Africa/Abidjan", "Accra, Abidjan"], ["Europe/London", "London, Lisbon"],
  ["Europe/Amsterdam", "Amsterdam, Berlin, Rome"], ["Africa/Johannesburg", "Johannesburg, Cape Town"],
  ["Europe/Athens", "Athens, Bucharest, Kyiv"], ["Europe/Moscow", "Moscow, St. Petersburg"],
  ["Asia/Tehran", "Tehran"], ["Asia/Dubai", "Dubai"], ["Asia/Kabul", "Kabul"],
  ["Asia/Karachi", "Karachi"], ["Asia/Kolkata", "India"], ["Asia/Kathmandu", "Nepal"],
  ["Asia/Dhaka", "Dhaka"], ["Asia/Yangon", "Yangon"], ["Asia/Bangkok", "Bangkok, Jakarta"],
  ["Asia/Shanghai", "China"], ["Asia/Tokyo", "Tokyo, Seoul"], ["Australia/Darwin", "Darwin"],
  ["Australia/Adelaide", "Adelaide"], ["Australia/Brisbane", "Brisbane"],
  ["Australia/Sydney", "Sydney"], ["Australia/Lord_Howe", "Lord Howe Island"],
  ["Pacific/Noumea", "Nouméa"], ["Pacific/Auckland", "Auckland, Wellington"],
  ["Pacific/Chatham", "Chatham Islands"], ["Pacific/Kiritimati", "Kiritimati"],
] as const;

function getRoute(): AppRoute {
  const [path, query] = window.location.hash.replace(/^#\/?/, "").split("?");
  const [page, id, entry] = path.split("/");
  const exerciseId = id ? Number(id) : undefined;
  const entryId = entry ? Number(entry) : undefined;
  if (page === "exercise" && exerciseId) return { name: "exercise", exerciseId };
  if (page === "new-entry" && exerciseId) return { name: "new-entry", exerciseId, returnToHome: new URLSearchParams(query).get("from") === "home" };
  if (page === "exercise-settings" && exerciseId) return { name: "exercise-settings", exerciseId };
  if (page === "weeks" && exerciseId) return { name: "weeks", exerciseId };
  if (page === "results" && exerciseId) return { name: "results", exerciseId };
  if (page === "edit-entry" && exerciseId && entryId) return { name: "edit-entry", exerciseId, entryId };
  if (page === "new-exercise" || page === "settings") return { name: page };
  return { name: "home" };
}

function navigate(route: AppRoute) {
  const path = route.exerciseId ? `${route.name}/${route.exerciseId}${route.entryId ? `/${route.entryId}` : ""}` : route.name === "home" ? "" : route.name;
  window.location.hash = `/${path}${route.returnToHome ? "?from=home" : ""}`;
}

function AnimatedNumber({ value, empty = "—" }: { value: number; empty?: string }) {
  const previousValue = useRef(value);
  const [displayValue, setDisplayValue] = useState(value);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    const from = previousValue.current;
    previousValue.current = value;
    if (from === value) {
      setDisplayValue(value);
      return;
    }
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setDisplayValue(value);
      return;
    }

    const startedAt = performance.now();
    const duration = 480;
    let animationFrame = 0;
    setIsAnimating(true);
    const tick = (now: number) => {
      const progress = Math.min((now - startedAt) / duration, 1);
      const eased = 1 - (1 - progress) ** 3;
      setDisplayValue(Math.round(from + (value - from) * eased));
      if (progress < 1) animationFrame = requestAnimationFrame(tick);
      else setIsAnimating(false);
    };
    animationFrame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationFrame);
  }, [value]);

  const text = value === 0 && !isAnimating ? empty : formatNumber(displayValue);
  return <span className={`animated-number${isAnimating ? " is-changing" : ""}`}>{text}</span>;
}

function Header({ title, back, action }: { title: string; back?: () => void; action?: React.ReactNode }) {
  return <header className="topbar">
    {back ? <button className="icon-button back-button" aria-label={t("common.goBack")} onClick={back}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M12 5l-7 7 7 7" /></svg></button> : <span className="brand-mark">R</span>}
    <h1>{title}</h1>
    {action ?? <span className="topbar-space" />}
  </header>;
}

function Loading() { return <div className="loading">{t("common.loading")}</div>; }

function ErrorNotice({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error-notice"><span>{message}</span>{retry && <button onClick={retry}>{t("common.tryAgain")}</button>}</div>;
}

function ConnectionErrorPage({ message, retry }: { message: string; retry: () => void }) {
  return <main className="app-shell connection-error-page">
    <Header title={t("app.title")} />
    <section className="connection-error" aria-live="polite">
      <div className="connection-error-icon" aria-hidden="true">
        <svg viewBox="0 0 96 96" fill="none">
          <circle cx="27" cy="48" r="9" />
          <circle cx="69" cy="48" r="9" />
          <path d="M37 48h8M51 48h8" />
          <path className="connection-error-break" d="m48 38-5 10h8l-5 10" />
        </svg>
      </div>
      <p className="eyebrow">{t("connection.eyebrow")}</p>
      <h2>{t("connection.title")}</h2>
      <p className="connection-error-copy">{t("connection.copy")}</p>
      <p className="connection-error-detail">{message}</p>
      <button className="primary-button connection-error-retry" onClick={retry}>
        {t("common.tryAgain")}
      </button>
    </section>
  </main>;
}

function App() {
  const [route, setRoute] = useState(getRoute);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string>();

  const initialise = useCallback(async () => {
    setError(undefined);
    try { await appDataCache.resolveUser(); setIsReady(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadFailed")); }
  }, []);

  useEffect(() => { void initialise(); }, [initialise]);
  useEffect(() => {
    const onHashChange = () => setRoute(getRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  if (error) return <ConnectionErrorPage message={error} retry={initialise} />;
  if (!isReady) return <main className="app-shell"><Header title={t("app.title")} /><Loading /></main>;

  const go = (next: AppRoute) => navigate(next);
  if (route.name === "new-exercise") return <NewExercisePage back={() => go({ name: "home" })} done={() => go({ name: "home" })} />;
  if (route.name === "settings") return <SettingsPage back={() => go({ name: "home" })} />;
  if (route.exerciseId && route.name === "new-entry") return <EntryEditorPage exerciseId={route.exerciseId} back={() => go(route.returnToHome ? { name: "home" } : { name: "exercise", exerciseId: route.exerciseId })} done={() => go(route.returnToHome ? { name: "home" } : { name: "exercise", exerciseId: route.exerciseId })} />;
  if (route.exerciseId && route.name === "exercise-settings") return <ExerciseSettingsPage exerciseId={route.exerciseId} back={() => go({ name: "exercise", exerciseId: route.exerciseId })} home={() => go({ name: "home" })} />;
  if (route.exerciseId && route.name === "weeks") return <WeeksPage exerciseId={route.exerciseId} back={() => go({ name: "exercise", exerciseId: route.exerciseId })} />;
  if (route.exerciseId && route.name === "results") return <ResultsPage exerciseId={route.exerciseId} back={() => go({ name: "exercise", exerciseId: route.exerciseId })} edit={(entryId) => go({ name: "edit-entry", exerciseId: route.exerciseId, entryId })} />;
  if (route.exerciseId && route.entryId && route.name === "edit-entry") return <EntryEditorPage exerciseId={route.exerciseId} entryId={route.entryId} back={() => go({ name: "results", exerciseId: route.exerciseId })} done={() => go({ name: "results", exerciseId: route.exerciseId })} />;
  if (route.exerciseId && route.name === "exercise") return <ExercisePage exerciseId={route.exerciseId} back={() => go({ name: "home" })} addEntry={() => go({ name: "new-entry", exerciseId: route.exerciseId })} settings={() => go({ name: "exercise-settings", exerciseId: route.exerciseId })} allWeeks={() => go({ name: "weeks", exerciseId: route.exerciseId })} allResults={() => go({ name: "results", exerciseId: route.exerciseId })} edit={(entryId) => go({ name: "edit-entry", exerciseId: route.exerciseId, entryId })} />;
  return <HomePage open={(id) => go({ name: "exercise", exerciseId: id })} add={() => go({ name: "new-exercise" })} settings={() => go({ name: "settings" })} />;
}

function HomePage({ open, add, settings }: { open: (id: number) => void; add: () => void; settings: () => void }) {
  const [exercises, setExercises] = useState<ExerciseSummary[] | undefined>(() => appDataCache.peekDashboard());
  const [error, setError] = useState<string>();
  const load = useCallback(async (force = false) => {
    setError(undefined);
    try { setExercises(await appDataCache.loadDashboard(force)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadExercises")); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return <main className="app-shell">
    <header className="topbar home-topbar"><div className="home-brand"><img src={repkaLogo} alt="" /><h1>{t("app.brand")}</h1></div><button className="icon-button home-settings-button" aria-label={t("home.settingsLabel")} onClick={settings}><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06-.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg></button></header>
    {error && !exercises ? <ErrorNotice message={error} retry={() => load(true)} /> : !exercises ? <Loading /> : exercises.length === 0 ? <EmptyState onAdd={add} /> : <section className="exercise-list" aria-label={t("home.exercisesLabel")}>
      {exercises.map((exercise) => <HomeExerciseCard key={exercise.id} exercise={exercise} open={open} addEntry={(id) => navigate({ name: "new-entry", exerciseId: id, returnToHome: true })} />)}
    </section>}
    <button className="primary-button floating-button" onClick={add}><span>+</span> {t("home.newExercise")}</button>
  </main>;
}

function recentDates(today: string) {
  const end = new Date(`${today}T12:00:00`);
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(end);
    date.setDate(date.getDate() - (6 - index));
    return isoDate(date);
  });
}

function HomeExerciseCard({ exercise, open, addEntry }: { exercise: ExerciseSummary; open: (id: number) => void; addEntry: (id: number) => void }) {
  const days = recentDates(exercise.stats.today);
  const totals = new Map(exercise.history.map((day) => [day.date, day.total_reps]));
  const values = days.map((day) => totals.get(day) ?? 0);
  const latest = exercise.stats.last_entry;

  return <article className="home-exercise-card">
    <div className="home-exercise-header">
      <button className="home-exercise-open" onClick={() => open(exercise.id)} aria-label={t("home.openExercise", { name: exercise.name })}>
        <span className="home-exercise-summary">
          <strong>{exercise.name}</strong>
          {latest ? <span className="home-exercise-last"><span>{formatSets(latest.reps)}</span><i>·</i><span>{relativeEntryTime(latest.created_at)}</span></span> : <span className="home-exercise-last is-empty">{t("common.noResultsYet")}</span>}
        </span>
        <span className={`home-today-total ${exercise.stats.today_reps > 0 ? "has-reps" : ""}`}>
          <b><AnimatedNumber value={exercise.stats.today_reps} /></b>
          <small>{t("common.today")}</small>
        </span>
      </button>
    </div>
    <div className="home-activity-row">
      <HomeActivityBars days={days} values={values} today={exercise.stats.today} />
      <button className="home-activity-add" onClick={() => addEntry(exercise.id)} aria-label={t("home.addResultFor", { name: exercise.name })}><span aria-hidden="true">+</span></button>
    </div>
  </article>;
}

function HomeActivityBars({ days, values, today }: { days: string[]; values: number[]; today: string }) {
  const maximum = Math.max(...values, 1);
  return <div className="home-activity-bars" aria-label={t("home.activityLabel")}>
    {days.map((day, index) => {
      const value = values[index];
      const active = value > 0;
      const isToday = day === today;
      const label = formatWeekdayNarrow(new Date(`${day}T12:00:00`));
      return <span className={`home-activity-day ${active ? "has-activity" : ""} ${isToday ? "is-today" : ""}`} key={day}>
        <i style={{ height: `${active ? Math.max(3, (value / maximum) * 32) : 2}px` }} />
        <small>{label}</small>
      </span>;
    })}
  </div>;
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return <section className="empty-state"><div className="empty-orb">↗</div><h3>{t("home.emptyTitle")}</h3><p>{t("home.emptyCopy")}</p><button className="primary-button" onClick={onAdd}>{t("home.emptyCta")}</button></section>;
}

function NewExercisePage({ back, done }: { back: () => void; done: () => void }) {
  const [name, setName] = useState(""); const [error, setError] = useState<string>(); const [saving, setSaving] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setSaving(true); setError(undefined); try { await api.createExercise(name.trim()); appDataCache.invalidateExercises(); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.createExercise")); } finally { setSaving(false); } };
  return <main className="app-shell"><Header title={t("newExercise.title")} back={back} /><form className="screen-form new-exercise-form" onSubmit={submit}><label>{t("newExercise.nameLabel")}<input autoFocus value={name} onChange={(event) => setName(event.target.value)} placeholder={t("newExercise.nameLabel")} maxLength={255} /></label>{error && <ErrorNotice message={error} />}<button className="primary-button" disabled={!name.trim() || saving}>{saving ? t("newExercise.creating") : t("newExercise.create")}</button></form></main>;
}

function ExercisePage({ exerciseId, back, addEntry, settings, allWeeks, allResults, edit }: { exerciseId: number; back: () => void; addEntry: () => void; settings: () => void; allWeeks: () => void; allResults: () => void; edit: (entryId: number) => void }) {
  const [detail, setDetail] = useState<ExerciseDetail | undefined>(() => appDataCache.peekDetail(exerciseId));
  const [history, setHistory] = useState<HistoryDay[]>();
  const [loadingFullHistory, setLoadingFullHistory] = useState(false);
  const [recentEntries, setRecentEntries] = useState<Record<string, ExerciseEntry[]>>({});
  const [loadingRecentDays, setLoadingRecentDays] = useState<string[]>([]);
  const [recentError, setRecentError] = useState<string>();
  const [error, setError] = useState<string>();
  const [period, setPeriod] = useState<ChartPeriod>("7d");
  const load = useCallback(async (force = false) => { setError(undefined); try { setDetail(await appDataCache.loadDetail(exerciseId, force)); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadExercise")); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    setDetail(appDataCache.peekDetail(exerciseId));
    setHistory(undefined);
    setRecentEntries({});
    setLoadingRecentDays([]);
    setRecentError(undefined);
    setPeriod("7d");
  }, [exerciseId]);
  useEffect(() => {
    if (!detail || detail.exercise.id !== exerciseId) return;
    const dates = detail.history.slice(0, 3).map((day) => day.date);
    let current = true;
    setRecentEntries({});
    setRecentError(undefined);
    setLoadingRecentDays(dates);
    void Promise.all(dates.map(async (date) => [date, await appDataCache.loadEntriesForDay(exerciseId, date)] as const))
      .then((dayEntries) => { if (current) setRecentEntries(Object.fromEntries(dayEntries)); })
      .catch((reason) => { if (current) setRecentError(reason instanceof Error ? reason.message : t("errors.loadRecentResults")); })
      .finally(() => { if (current) setLoadingRecentDays([]); });
    return () => { current = false; };
  }, [detail, exerciseId]);
  const loadFullHistory = useCallback(async () => {
    setLoadingFullHistory(true);
    try { setHistory(await appDataCache.loadFullHistory(exerciseId)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadFullHistory")); }
    finally { setLoadingFullHistory(false); }
  }, [exerciseId]);
  const changePeriod = (nextPeriod: ChartPeriod) => {
    setPeriod(nextPeriod);
    if (nextPeriod === "all") void loadFullHistory();
  };
  const visibleDetail = detail?.exercise.id === exerciseId ? detail : undefined;
  if (error && !visibleDetail) return <main className="app-shell"><Header title={t("exercise.fallbackTitle")} back={back} /><ErrorNotice message={error} retry={() => load(true)} /></main>;
  if (!visibleDetail) return <main className="app-shell"><Header title={t("exercise.fallbackTitle")} back={back} /><Loading /></main>;
  const exerciseHistory = period === "all" && history ? history : visibleDetail.history;
  const recentDays = visibleDetail.history.slice(0, 3);
  return <main className="app-shell exercise-page">
    <Header title={visibleDetail.exercise.name} back={back} action={<button className="icon-button settings-button" aria-label={t("exercise.settingsLabel")} onClick={settings}><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="5" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="12" cy="19" r="1.5" /></svg></button>} />
    <section className="dashboard-card today-card">
      <div className="dashboard-label">{t("common.today")}</div>
      <div className="today-card-content">
        <div><strong><AnimatedNumber value={visibleDetail.stats.today_reps} /></strong><small>{visibleDetail.stats.today_reps > 0 ? t("common.reps") : t("common.noResultsYet")}</small></div>
        {visibleDetail.stats.last_entry && <div className="latest-result"><span>{t("exercise.latest")}</span><b>{formatSets(visibleDetail.stats.last_entry.reps)}</b><small>{relativeEntryTime(visibleDetail.stats.last_entry.created_at)}</small></div>}
      </div>
    </section>
    <button className="primary-button overview-add-button" onClick={addEntry}>{t("exercise.addResult")}</button>
    <LastSevenDays days={exerciseHistory} today={visibleDetail.stats.today} period={period} setPeriod={changePeriod} loadingAll={loadingFullHistory} />
    <WeeklyProgress days={exerciseHistory} today={visibleDetail.stats.today} onShowAll={allWeeks} />
    <section className="dashboard-card results-panel"><div className="section-heading"><h3>{t("exercise.recentTitle")}</h3></div>{recentDays.length === 0 ? <p className="muted">{t("exercise.recentEmpty")}</p> : <><RecentResults days={recentDays} entriesByDate={recentEntries} loadingDates={loadingRecentDays} timezone={visibleDetail.timezone} onSelect={edit} />{recentError && <p className="result-load-error">{recentError}</p>}<div className="results-footer"><button className="text-button" onClick={allResults}>{t("exercise.allResults")}</button></div></>}</section>
  </main>;
}

type Week = { start: string; end: string; total: number };
type ChartPeriod = "7d" | "30d" | "all";

function isoDate(value: Date) {
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${value.getFullYear()}-${month}-${day}`;
}

function startOfWeek(value: string) {
  const date = new Date(`${value}T12:00:00`);
  const mondayOffset = (date.getDay() + 6) % 7;
  date.setDate(date.getDate() - mondayOffset);
  return date;
}

function buildWeeks(days: HistoryDay[], today: string, minimumWeeks = 1) {
  const totals = new Map(days.map((day) => [day.date, day.total_reps]));
  const currentStart = startOfWeek(today);
  const oldestStart = startOfWeek(days.reduce((oldest, day) => day.date < oldest ? day.date : oldest, today));
  const count = Math.max(minimumWeeks, Math.floor((currentStart.getTime() - oldestStart.getTime()) / (7 * 24 * 60 * 60 * 1000)) + 1);
  return Array.from({ length: count }, (_, index) => {
    const start = new Date(currentStart); start.setDate(start.getDate() - index * 7);
    const end = new Date(start); end.setDate(end.getDate() + 6);
    let total = 0;
    for (let day = new Date(start); day <= end; day.setDate(day.getDate() + 1)) total += totals.get(isoDate(day)) ?? 0;
    return { start: isoDate(start), end: isoDate(end), total };
  });
}

type ActivityDatum = { key: string; label: string; detail: string; total: number; isToday?: boolean };

function buildDailyActivity(days: HistoryDay[], today: string, count: number): ActivityDatum[] {
  const totals = new Map(days.map((day) => [day.date, day.total_reps]));
  const end = new Date(`${today}T12:00:00`);
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(end); date.setDate(date.getDate() - (count - index - 1));
    const dateString = isoDate(date);
    const label = count === 7 ? formatWeekdayShort(date) : formatDayNumeric(date);
    return { key: dateString, label, detail: formatDate(dateString), total: totals.get(dateString) ?? 0, isToday: dateString === today };
  });
}

function buildMonthlyActivity(days: HistoryDay[], today: string): ActivityDatum[] {
  const totals = new Map<string, number>();
  days.forEach((day) => { const key = day.date.slice(0, 7); totals.set(key, (totals.get(key) ?? 0) + day.total_reps); });
  const firstDate = days.length ? new Date(`${days.reduce((oldest, day) => day.date < oldest ? day.date : oldest, today)}T12:00:00`) : new Date(`${today}T12:00:00`);
  const cursor = new Date(firstDate.getFullYear(), firstDate.getMonth(), 1);
  const last = new Date(`${today}T12:00:00`); last.setDate(1);
  const result: ActivityDatum[] = [];
  while (cursor <= last) {
    const key = `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}`;
    const label = formatMonth(cursor);
    result.push({ key, label, detail: label, total: totals.get(key) ?? 0 });
    cursor.setMonth(cursor.getMonth() + 1);
  }
  return result;
}

function axisIndexes(length: number, maximum = 4) {
  if (length <= maximum) return new Set(Array.from({ length }, (_, index) => index));
  return new Set(Array.from({ length: maximum }, (_, index) => Math.round(index * (length - 1) / (maximum - 1))));
}

function LastSevenDays({ days, today, period, setPeriod, loadingAll }: { days: HistoryDay[]; today: string; period: ChartPeriod; setPeriod: (period: ChartPeriod) => void; loadingAll: boolean }) {
  const chartDays = period === "all" ? buildMonthlyActivity(days, today) : buildDailyActivity(days, today, period === "7d" ? 7 : 30);
  const [selectedKey, setSelectedKey] = useState<string>();
  const selected = chartDays.find((day) => day.key === selectedKey);
  const max = Math.max(...chartDays.map((day) => day.total), 1);
  const periodTotal = chartDays.reduce((sum, day) => sum + day.total, 0);
  const visibleAxis = period === "7d" ? new Set(chartDays.map((_, index) => index)) : axisIndexes(chartDays.length);
  return <section className="dashboard-card progress-card"><div className="progress-card-header"><div><div className="dashboard-label">{t("progress.title")}</div><div className="progress-period-total"><strong><AnimatedNumber value={periodTotal} empty="0" /></strong><span>{t("common.reps")}</span></div></div><div className="period-tabs">{(["7d", "30d", "all"] as ChartPeriod[]).map((item) => <button type="button" key={item} className={period === item ? "is-active" : ""} onClick={() => { setSelectedKey(undefined); setPeriod(item); }}>{item === "all" ? t("progress.periodAll") : item}</button>)}</div></div>{loadingAll ? <p className="muted">{t("progress.loadingHistory")}</p> : <><div className={`daily-bars activity-${period}`}>{chartDays.map((day, index) => <button type="button" className={`daily-bar ${day.total > 0 ? "has-activity" : ""} ${visibleAxis.has(index) ? "has-axis" : ""} ${selected?.key === day.key ? "is-selected" : ""}`} key={day.key} onClick={() => setSelectedKey(day.key)} aria-label={t("progress.barLabel", { detail: day.detail, total: formatNumber(day.total) })} aria-pressed={selected?.key === day.key}>{period === "7d" && <strong>{day.total}</strong>}<div className="bar-track"><i style={{ height: day.total > 0 ? `${Math.max((day.total / max) * 100, 6)}%` : "2px" }} /></div>{visibleAxis.has(index) && <span>{day.label}</span>}</button>)}</div><p className="activity-detail" aria-live="polite">{selected && <>{selected.detail} <b>{t("progress.selectedTotal", { total: formatNumber(selected.total) })}</b></>}</p></>}</section>;
}

function WeeklyProgress({ days, today, onShowAll }: { days: HistoryDay[]; today: string; onShowAll: () => void }) {
  const weeks = buildWeeks(days, today, 5).slice(0, 5);
  const [current, previous] = weeks;
  const percent = previous.total > 0 ? Math.round(((current.total - previous.total) / previous.total) * 100) : null;
  const maximum = Math.max(...weeks.map((week) => week.total), 1);
  if (!days.length) return <section className="dashboard-card weekly-progress"><div className="section-heading"><h3>{t("weekly.title")}</h3><button className="text-button" onClick={onShowAll}>{t("weekly.allWeeks")}</button></div><div className="chart-empty">{t("weekly.empty")}</div></section>;
  return <section className="dashboard-card weekly-progress"><div className="section-heading"><h3>{t("weekly.title")}</h3></div><div className="week-summary"><div className="week-summary-main"><span>{formatWeekRange(current.start, current.end)}</span><div className="week-summary-total"><strong><AnimatedNumber value={current.total} empty="0" /></strong><small>{t("common.reps")}</small></div></div>{percent !== null && <div className="week-summary-change"><strong className={percent >= 0 ? "positive" : "negative"}>{formatPercentChange(percent)}</strong><span>{t("weekly.vsLastWeek")}</span></div>}</div><div className="week-list">{weeks.slice(1).map((week, index) => <WeekRow key={week.start} week={week} older={weeks[index + 2]} maximum={maximum} />)}</div><div className="week-footer"><div className="week-footer-stats"><div><small>{t("weekly.best")}</small><strong>{formatNumber(Math.max(...weeks.map((week) => week.total)))}</strong></div><div><small>{t("weekly.avg")}</small><strong>{formatNumber(Math.round(weeks.reduce((sum, week) => sum + week.total, 0) / weeks.length))}</strong></div></div><button className="text-button" onClick={onShowAll}>{t("weekly.allWeeks")}</button></div></section>;
}

function WeekRow({ week, older, maximum }: { week: Week; older?: Week; maximum: number }) {
  const change = older && older.total > 0 ? Math.round(((week.total - older.total) / older.total) * 100) : null;
  const barWidth = week.total > 0 ? Math.max(4, Math.round((week.total / maximum) * 100)) : 0;
  const changeLabel = formatPercentChange(change);
  return <div className="week-row"><div className="week-label"><strong>{formatWeekRange(week.start, week.end)}</strong></div><div className="week-bar" aria-hidden="true"><i style={{ width: `${barWidth}%` }} /></div><span className="week-total">{formatNumber(week.total)}</span><b className={`week-change ${change === null ? "neutral" : change >= 0 ? "positive" : "negative"}`}>{changeLabel}</b></div>;
}

function ResultRows({ entries, timezone, onSelect }: { entries: ExerciseEntry[]; timezone: string; onSelect: (entryId: number) => void }) {
  return <>{entries.map((entry) => <button className="result-row result-button" key={entry.id} onClick={() => onSelect(entry.id)} aria-label={t("results.openResult", { sets: formatSets(entry.reps), total: formatNumber(totalReps(entry)) })}><div><strong>{formatSets(entry.reps)}</strong><small>{formatTime(entry.created_at, timezone)}</small></div><b>{formatNumber(totalReps(entry))} <small>{t("common.reps")}</small></b><span className="result-chevron" aria-hidden="true">›</span></button>)}</>;
}

function DayTotal({ day }: { day: HistoryDay }) {
  return <span className="result-day-total"><strong>{formatNumber(day.total_reps)}</strong> {t("common.reps")} <small>· {t("results.resultsCount", { count: day.entries_count })}</small></span>;
}

function RecentResults({ days, entriesByDate, loadingDates, timezone, onSelect }: { days: HistoryDay[]; entriesByDate: Record<string, ExerciseEntry[]>; loadingDates: string[]; timezone: string; onSelect: (entryId: number) => void }) {
  return <div className="result-list">{days.map((day) => <section className="result-day" key={day.date}><h4><span className="result-date">{formatDate(day.date)}</span><DayTotal day={day} /></h4>{loadingDates.includes(day.date) ? <p className="result-loading">{t("exercise.loadingResults")}</p> : <ResultRows entries={entriesByDate[day.date] ?? []} timezone={timezone} onSelect={onSelect} />}</section>)}</div>;
}

function HistoryDays({ days, expandedDate, entriesByDate, loadingDates, errors, timezone, onSelect, onToggle }: { days: HistoryDay[]; expandedDate?: string; entriesByDate: Record<string, ExerciseEntry[]>; loadingDates: string[]; errors: Record<string, string>; timezone: string; onSelect: (entryId: number) => void; onToggle: (date: string) => void }) {
  return <div className="history-day-list">{days.map((day) => {
    const expanded = day.date === expandedDate;
    return <section className={`history-day ${expanded ? "is-expanded" : ""}`} key={day.date}>
      <button className="history-day-toggle" onClick={() => onToggle(day.date)} aria-expanded={expanded}>
        <span className="history-day-date">{formatDate(day.date)}</span><DayTotal day={day} /><span className="history-day-chevron" aria-hidden="true">⌄</span>
      </button>
      {expanded && <div className="history-day-entries">{loadingDates.includes(day.date) ? <p className="result-loading">{t("exercise.loadingResults")}</p> : errors[day.date] ? <p className="result-load-error">{errors[day.date]}</p> : <ResultRows entries={entriesByDate[day.date] ?? []} timezone={timezone} onSelect={onSelect} />}</div>}
    </section>;
  })}</div>;
}

function WeeksPage({ exerciseId, back }: { exerciseId: number; back: () => void }) {
  const [days, setDays] = useState<HistoryDay[] | undefined>(() => appDataCache.peekFullHistory(exerciseId)); const [today, setToday] = useState<string | undefined>(() => appDataCache.peekSettings()?.today); const [error, setError] = useState<string>();
  const load = useCallback(async (force = false) => { setError(undefined); try { const [history, settings] = await Promise.all([appDataCache.loadFullHistory(exerciseId, force), appDataCache.loadSettings(force)]); setDays(history); setToday(settings.today); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadWeeklyHistory")); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  if (!days || !today) return <main className="app-shell"><Header title={t("weeks.title")} back={back} />{error ? <ErrorNotice message={error} retry={() => load(true)} /> : <Loading />}</main>;
  const weeks = buildWeeks(days, today);
  const maximum = Math.max(...weeks.map((week) => week.total), 1);
  return <main className="app-shell detail-list-page"><Header title={t("weeks.title")} back={back} />{!days.length ? <section className="dashboard-card"><div className="chart-empty">{t("weeks.empty")}</div></section> : <section className="dashboard-card weekly-progress full-history"><div className="section-heading"><h3>{t("weeks.historyTitle")}</h3><span>{t("weeks.weeksCount", { count: weeks.length })}</span></div><div className="week-list">{weeks.map((week, index) => <WeekRow key={week.start} week={week} older={weeks[index + 1]} maximum={maximum} />)}</div></section>}</main>;
}

const HISTORY_DAYS_PAGE_SIZE = 20;

function ResultsPage({ exerciseId, back, edit }: { exerciseId: number; back: () => void; edit: (entryId: number) => void }) {
  const [days, setDays] = useState<HistoryDay[] | undefined>(() => appDataCache.peekResultsHistory(exerciseId)?.days);
  const [timezone, setTimezone] = useState<string | undefined>(() => appDataCache.peekSettings()?.timezone);
  const [hasMore, setHasMore] = useState(() => appDataCache.peekResultsHistory(exerciseId)?.hasMore ?? false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [expandedDate, setExpandedDate] = useState<string>();
  const [entriesByDate, setEntriesByDate] = useState<Record<string, ExerciseEntry[]>>({});
  const [loadingDates, setLoadingDates] = useState<string[]>([]);
  const [dayErrors, setDayErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string>();
  const load = useCallback(async (force = false) => {
    setError(undefined);
    try {
      const [history, settings] = await Promise.all([appDataCache.loadResultsHistory(exerciseId, HISTORY_DAYS_PAGE_SIZE, force), appDataCache.loadSettings(force)]);
      setDays(history.days); setTimezone(settings.timezone); setHasMore(history.hasMore);
      setExpandedDate(undefined); setEntriesByDate({}); setLoadingDates([]); setDayErrors({});
    } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadResults")); }
  }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  const loadMore = async () => {
    if (!days || loadingMore) return;
    setLoadingMore(true); setError(undefined);
    try {
      const nextDays = await api.history(exerciseId, HISTORY_DAYS_PAGE_SIZE, days.length);
      const history = { days: [...days, ...nextDays], hasMore: nextDays.length === HISTORY_DAYS_PAGE_SIZE };
      setDays(history.days); setHasMore(history.hasMore); appDataCache.saveResultsHistory(exerciseId, history);
    } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadMoreDays")); }
    finally { setLoadingMore(false); }
  };
  const toggleDay = async (date: string) => {
    if (expandedDate === date) { setExpandedDate(undefined); return; }
    setExpandedDate(date);
    if (entriesByDate[date] || loadingDates.includes(date)) return;
    setLoadingDates((current) => [...current, date]);
    setDayErrors((current) => { const { [date]: _, ...rest } = current; return rest; });
    try {
      const entries = await appDataCache.loadEntriesForDay(exerciseId, date);
      setEntriesByDate((current) => ({ ...current, [date]: entries }));
    } catch (reason) { setDayErrors((current) => ({ ...current, [date]: reason instanceof Error ? reason.message : t("errors.loadDayResults") })); }
    finally { setLoadingDates((current) => current.filter((item) => item !== date)); }
  };
  if (!days || !timezone) return <main className="app-shell"><Header title={t("results.title")} back={back} />{error ? <ErrorNotice message={error} retry={() => load(true)} /> : <Loading />}</main>;
  return <main className="app-shell detail-list-page"><Header title={t("results.title")} back={back} /><section className="dashboard-card results-panel"><div className="section-heading"><h3>{t("results.historyTitle")}</h3>{days.length > 0 && <span>{t("results.daysCount", { count: days.length })}</span>}</div>{days.length ? <><HistoryDays days={days} expandedDate={expandedDate} entriesByDate={entriesByDate} loadingDates={loadingDates} errors={dayErrors} timezone={timezone} onSelect={edit} onToggle={toggleDay} />{error && <ErrorNotice message={error} retry={loadMore} />}{hasMore && <div className="results-footer"><button className="text-button" onClick={() => void loadMore()} disabled={loadingMore}>{loadingMore ? t("common.loadingShort") : t("results.loadMore")}</button></div>}</> : <p className="muted">{t("results.empty")}</p>}</section></main>;
}

function EntryEditorPage({ exerciseId, entryId, back, done }: { exerciseId: number; entryId?: number; back: () => void; done: () => void }) {
  const isEditing = entryId !== undefined;
  const deviceToday = isoDate(new Date());
  const [reps, setReps] = useState<number[]>([10]); const [quickInput, setQuickInput] = useState("10"); const [quickError, setQuickError] = useState<string>(); const [date, setDate] = useState(deviceToday); const [today, setToday] = useState(deviceToday); const [exerciseName, setExerciseName] = useState(() => appDataCache.peekExercise(exerciseId)?.name ?? ""); const [loading, setLoading] = useState(isEditing); const [saving, setSaving] = useState(false); const [error, setError] = useState<string>();
  const syncSets = (next: number[]) => { setReps(next); setQuickInput(formatSets(next)); setQuickError(undefined); };
  useEffect(() => {
    if (!isEditing) return;
    void (async () => { try { const [settings, detail] = await Promise.all([appDataCache.loadSettings(), appDataCache.loadDetail(exerciseId)]); setToday(settings.today); setExerciseName(detail.exercise.name); const entry = appDataCache.peekEntry(exerciseId, entryId) ?? (await appDataCache.loadFullEntries(exerciseId)).find((item) => item.id === entryId); if (!entry) throw new Error(t("errors.resultNotFound")); syncSets(entry.reps); setDate(entry.performed_on); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadResult")); } finally { setLoading(false); } })();
  }, [entryId, exerciseId, isEditing]);
  const updateSet = (index: number, value: number) => syncSets(reps.map((setReps, itemIndex) => itemIndex === index ? value : setReps));
  const applyQuickInput = (value: string) => { setQuickInput(value); try { const next = parseQuickResult(value); setReps(next); setQuickError(undefined); } catch { setQuickError(undefined); } };
  const validateQuickInput = () => { try { const next = parseQuickResult(quickInput); syncSets(next); return next; } catch (reason) { setQuickError(reason instanceof Error ? reason.message : t("errors.invalidResult")); return undefined; } };
  const save = async (event: FormEvent) => { event.preventDefault(); const parsed = validateQuickInput(); if (!date || !parsed) return; setSaving(true); setError(undefined); try { if (entryId === undefined) await api.createEntry(exerciseId, parsed, date); else await api.updateEntry(entryId, parsed, date); appDataCache.invalidateExercise(exerciseId); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.saveResult")); } finally { setSaving(false); } };
  const remove = async () => { if (!entryId || !window.confirm(t("entry.deleteConfirm"))) return; setSaving(true); try { await api.deleteEntry(entryId); appDataCache.invalidateExercise(exerciseId); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.deleteResult")); setSaving(false); } };
  const total = reps.reduce((sum, value) => sum + (Number.isFinite(value) ? value : 0), 0);
  if (loading) return <main className="app-shell"><Header title={isEditing ? t("entry.editTitle") : t("entry.addTitle")} back={back} /><Loading /></main>;
  if (error && !date) return <main className="app-shell"><Header title={isEditing ? t("entry.editTitle") : t("entry.addTitle")} back={back} /><ErrorNotice message={error} /></main>;
  return <main className="app-shell">
    <Header title={isEditing ? t("entry.editTitle") : t("entry.addTitle")} back={back} />
    {exerciseName && <p className="entry-exercise-context" title={exerciseName}>{exerciseName}</p>}
    <form className="entry-editor" onSubmit={save}>
      <section className="entry-composer">
        <label className="quick-entry">
          <span>{t("entry.quickLabel")}</span>
          <input value={quickInput} onChange={(event) => applyQuickInput(event.target.value)} onBlur={validateQuickInput} placeholder={t("entry.quickPlaceholder")} autoComplete="off" />
          <small>{t("entry.quickHint")}</small>
        </label>
        {quickError && <p className="quick-error">{quickError}</p>}
        <section className="sets-panel">
          <div className="section-heading"><h3>{t("entry.setsTitle")}</h3><span>{t("entry.setsTotal", { total: formatNumber(total) })}</span></div>
          <div className="set-list">{reps.map((value, index) => <div className="set-editor" key={index}><span>{t("entry.setLabel", { index: index + 1 })}</span><button type="button" aria-label={t("entry.decreaseSet", { index: index + 1 })} onClick={() => updateSet(index, Math.max(1, value - 1))}>−</button><input aria-label={t("entry.repsForSet", { index: index + 1 })} type="number" inputMode="numeric" min="1" max="10000" value={value || ""} onChange={(event) => updateSet(index, Number(event.target.value))} /><button type="button" aria-label={t("entry.increaseSet", { index: index + 1 })} onClick={() => updateSet(index, Math.min(10000, value + 1))}>+</button><button className="remove-set" type="button" aria-label={t("entry.removeSet", { index: index + 1 })} disabled={reps.length === 1} onClick={() => syncSets(reps.filter((_, itemIndex) => itemIndex !== index))}>×</button></div>)}</div>
          <button className="add-set" type="button" onClick={() => syncSets([...reps, reps.at(-1) ?? 10])}>{t("entry.addSet")}</button>
        </section>
      </section>
      <label className="date-picker"><span>{t("entry.dateLabel")}</span><input id="entry-date" type="date" value={date} max={today} onChange={(event) => setDate(event.target.value)} /><small>{date === today ? t("common.today") : t("entry.selectedDateHint")}</small></label>
      {error && <ErrorNotice message={error} />}
      <button className="primary-button" disabled={saving}>{saving ? t("common.saving") : isEditing ? t("entry.saveChanges") : t("entry.save")}</button>
      {isEditing && <button className="danger-button editor-delete" type="button" disabled={saving} onClick={remove}>{t("entry.delete")}</button>}
    </form>
  </main>;
}

function ExerciseSettingsPage({ exerciseId, back, home }: { exerciseId: number; back: () => void; home: () => void }) {
  const [exercise, setExercise] = useState<Exercise>(); const [name, setName] = useState(""); const [error, setError] = useState<string>(); const [saving, setSaving] = useState(false);
  const load = useCallback(async () => { try { const detail = await appDataCache.loadDetail(exerciseId); setExercise(detail.exercise); setName(detail.exercise.name); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadSettings")); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  const saveName = async (event: FormEvent) => { event.preventDefault(); setSaving(true); setError(undefined); try { const updated = await api.updateExercise(exerciseId, name.trim()); setExercise(updated); setName(updated.name); appDataCache.invalidateExercises(); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.saveName")); } finally { setSaving(false); } };
  const toggleReport = async () => { if (!exercise) return; setSaving(true); setError(undefined); try { setExercise(await api.updateWeeklyReport(exerciseId, !exercise.weekly_report_enabled)); appDataCache.invalidateExercises(); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.updateReport")); } finally { setSaving(false); } };
  const archive = async () => { if (!window.confirm(t("exerciseSettings.archiveConfirm"))) return; try { await api.archiveExercise(exerciseId); appDataCache.invalidateExercises(); home(); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.archiveExercise")); } };
  if (!exercise) return <main className="app-shell"><Header title={t("exerciseSettings.title")} back={back} />{error ? <ErrorNotice message={error} retry={load} /> : <Loading />}</main>;
  return <main className="app-shell"><Header title={t("exerciseSettings.title")} back={back} /><form className="screen-form settings-form" onSubmit={saveName}><label>{t("exerciseSettings.nameLabel")}<input value={name} onChange={(event) => setName(event.target.value)} maxLength={255} /></label><button className="secondary-button" disabled={!name.trim() || saving}>{saving ? t("common.saving") : t("exerciseSettings.saveName")}</button></form><section className="settings-group"><div><strong>{t("exerciseSettings.weeklyTitle")}</strong><p>{t("exerciseSettings.weeklyCopy")}</p></div><button className={`switch ${exercise.weekly_report_enabled ? "is-on" : ""}`} aria-label={t("exerciseSettings.weeklyToggle")} onClick={toggleReport} disabled={saving}><span /></button></section>{error && <ErrorNotice message={error} />}<section className="danger-zone"><h3>{t("exerciseSettings.dangerTitle")}</h3><p>{t("exerciseSettings.dangerCopy")}</p><button className="danger-button" onClick={archive}>{t("exerciseSettings.archive")}</button></section></main>;
}

function SettingsPage({ back }: { back: () => void }) {
  const [settings, setSettings] = useState<Settings>(); const [timezone, setTimezone] = useState(""); const [language, setLanguage] = useState<Settings["language"]>("en"); const [error, setError] = useState<string>(); const [saving, setSaving] = useState(false);
  const load = useCallback(async () => { try { const response = await appDataCache.loadSettings(); setSettings(response); setTimezone(response.timezone); setLanguage(response.language); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.loadSettings")); } }, []);
  useEffect(() => { void load(); }, [load]);
  const save = async (event: FormEvent) => { event.preventDefault(); setSaving(true); setError(undefined); try { const updated = await api.updateSettings({ timezone: timezone.trim(), language }); setSettings(updated); appDataCache.saveSettings(updated); } catch (reason) { setError(reason instanceof Error ? reason.message : t("errors.saveSettings")); } finally { setSaving(false); } };
  if (!settings) return <main className="app-shell"><Header title={t("settings.title")} back={back} />{error ? <ErrorNotice message={error} retry={load} /> : <Loading />}</main>;
  const hasCurrentTimezone = timezoneOptions.some(([value]) => value === timezone);
  return <main className="app-shell"><Header title={t("settings.title")} back={back} /><form className="screen-form settings-form" onSubmit={save}><p className="eyebrow">{t("settings.eyebrow")}</p><label>{t("settings.timezoneLabel")}<select value={timezone} onChange={(event) => setTimezone(event.target.value)}>{!hasCurrentTimezone && <option value={timezone}>{timezone}</option>}{timezoneOptions.map(([value, label]) => <option key={value} value={value}>{label} — {value}</option>)}</select><small>{t("settings.timezoneHint")}</small></label><label>{t("settings.languageLabel")}<select value={language} onChange={(event) => setLanguage(event.target.value as Settings["language"])}>{languageOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>{error && <ErrorNotice message={error} />}<button className="primary-button" disabled={!timezone.trim() || saving}>{saving ? t("common.saving") : t("settings.save")}</button></form><p className="local-note">{t("settings.verifiedNote")}</p></main>;
}

export default App;
