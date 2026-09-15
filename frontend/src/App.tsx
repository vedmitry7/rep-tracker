import { FormEvent, useCallback, useEffect, useState } from "react";
import { api } from "./api";
import repkaLogo from "./assets/repka-logo.png";
import type { Exercise, ExerciseEntry, ExerciseStats, HistoryDay, Settings } from "./types";

type Route = "home" | "new-exercise" | "exercise" | "new-entry" | "exercise-settings" | "settings" | "weeks" | "results" | "edit-entry";

type AppRoute = { name: Route; exerciseId?: number; entryId?: number };
type ExerciseSummary = Exercise & { stats: ExerciseStats; history: HistoryDay[] };

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
  const [page, id, entry] = window.location.hash.replace(/^#\/?/, "").split("/");
  const exerciseId = id ? Number(id) : undefined;
  const entryId = entry ? Number(entry) : undefined;
  if (page === "exercise" && exerciseId) return { name: "exercise", exerciseId };
  if (page === "new-entry" && exerciseId) return { name: "new-entry", exerciseId };
  if (page === "exercise-settings" && exerciseId) return { name: "exercise-settings", exerciseId };
  if (page === "weeks" && exerciseId) return { name: "weeks", exerciseId };
  if (page === "results" && exerciseId) return { name: "results", exerciseId };
  if (page === "edit-entry" && exerciseId && entryId) return { name: "edit-entry", exerciseId, entryId };
  if (page === "new-exercise" || page === "settings") return { name: page };
  return { name: "home" };
}

function navigate(route: AppRoute) {
  const path = route.exerciseId ? `${route.name}/${route.exerciseId}${route.entryId ? `/${route.entryId}` : ""}` : route.name === "home" ? "" : route.name;
  window.location.hash = `/${path}`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", year: "numeric" }).format(new Date(`${value}T12:00:00`));
}

function formatTime(value: string, timeZone?: string) {
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", timeZone }).format(new Date(value));
}

function totalReps(entry: ExerciseEntry) { return entry.reps.reduce((sum, reps) => sum + reps, 0); }

function formatSets(reps: number[]) {
  return reps.length > 1 && reps.every((value) => value === reps[0]) ? `${reps.length} × ${reps[0]}` : reps.join(" + ");
}

function formatResultMoment(entry: ExerciseEntry, today: string, timezone: string) {
  const performedOn = entry.performed_on === today ? "Today" : formatDate(entry.performed_on);
  return `${performedOn}, ${formatTime(entry.created_at, timezone)}`;
}

function relativeEntryTime(value: string) {
  const elapsed = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.floor(elapsed / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "yesterday";
  if (days < 7) return `${days}d ago`;
  return formatDate(value.slice(0, 10));
}

function Header({ title, back, action }: { title: string; back?: () => void; action?: React.ReactNode }) {
  return <header className="topbar">
    {back ? <button className="icon-button back-button" aria-label="Go back" onClick={back}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M12 5l-7 7 7 7" /></svg></button> : <span className="brand-mark">R</span>}
    <h1>{title}</h1>
    {action ?? <span className="topbar-space" />}
  </header>;
}

function Loading() { return <div className="loading">Loading your training…</div>; }

function ErrorNotice({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error-notice"><span>{message}</span>{retry && <button onClick={retry}>Try again</button>}</div>;
}

function App() {
  const [route, setRoute] = useState(getRoute);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string>();

  const initialise = useCallback(async () => {
    setError(undefined);
    try { await api.resolveUser(); setIsReady(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not connect to the API."); }
  }, []);

  useEffect(() => { void initialise(); }, [initialise]);
  useEffect(() => {
    const onHashChange = () => setRoute(getRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  if (error) return <main className="app-shell"><Header title="Rep Tracker" /><ErrorNotice message={`API unavailable: ${error}`} retry={initialise} /><p className="hint">Start FastAPI on port 8000, then reload this page.</p></main>;
  if (!isReady) return <main className="app-shell"><Header title="Rep Tracker" /><Loading /></main>;

  const go = (next: AppRoute) => navigate(next);
  if (route.name === "new-exercise") return <NewExercisePage back={() => go({ name: "home" })} done={() => go({ name: "home" })} />;
  if (route.name === "settings") return <SettingsPage back={() => go({ name: "home" })} />;
  if (route.exerciseId && route.name === "new-entry") return <EntryEditorPage exerciseId={route.exerciseId} back={() => go({ name: "exercise", exerciseId: route.exerciseId })} done={() => go({ name: "exercise", exerciseId: route.exerciseId })} />;
  if (route.exerciseId && route.name === "exercise-settings") return <ExerciseSettingsPage exerciseId={route.exerciseId} back={() => go({ name: "exercise", exerciseId: route.exerciseId })} home={() => go({ name: "home" })} />;
  if (route.exerciseId && route.name === "weeks") return <WeeksPage exerciseId={route.exerciseId} back={() => go({ name: "exercise", exerciseId: route.exerciseId })} />;
  if (route.exerciseId && route.name === "results") return <ResultsPage exerciseId={route.exerciseId} back={() => go({ name: "exercise", exerciseId: route.exerciseId })} edit={(entryId) => go({ name: "edit-entry", exerciseId: route.exerciseId, entryId })} />;
  if (route.exerciseId && route.entryId && route.name === "edit-entry") return <EntryEditorPage exerciseId={route.exerciseId} entryId={route.entryId} back={() => go({ name: "results", exerciseId: route.exerciseId })} done={() => go({ name: "results", exerciseId: route.exerciseId })} />;
  if (route.exerciseId && route.name === "exercise") return <ExercisePage exerciseId={route.exerciseId} back={() => go({ name: "home" })} addEntry={() => go({ name: "new-entry", exerciseId: route.exerciseId })} settings={() => go({ name: "exercise-settings", exerciseId: route.exerciseId })} allWeeks={() => go({ name: "weeks", exerciseId: route.exerciseId })} allResults={() => go({ name: "results", exerciseId: route.exerciseId })} edit={(entryId) => go({ name: "edit-entry", exerciseId: route.exerciseId, entryId })} />;
  return <HomePage open={(id) => go({ name: "exercise", exerciseId: id })} add={() => go({ name: "new-exercise" })} settings={() => go({ name: "settings" })} />;
}

function HomePage({ open, add, settings }: { open: (id: number) => void; add: () => void; settings: () => void }) {
  const [exercises, setExercises] = useState<ExerciseSummary[]>();
  const [error, setError] = useState<string>();
  const load = useCallback(async () => {
    setError(undefined);
    try {
      const activeExercises = (await api.exercises()).filter((exercise) => !exercise.is_archived);
      setExercises(await Promise.all(activeExercises.map(async (exercise) => {
        const [stats, history] = await Promise.all([api.stats(exercise.id), api.history(exercise.id, 7)]);
        return { ...exercise, stats, history };
      })));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load exercises."); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return <main className="app-shell">
    <header className="topbar home-topbar"><div className="home-brand"><img src={repkaLogo} alt="" /><h1>Repka</h1></div><button className="icon-button home-settings-button" aria-label="Global settings" onClick={settings}><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06-.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg></button></header>
    {error ? <ErrorNotice message={error} retry={load} /> : !exercises ? <Loading /> : exercises.length === 0 ? <EmptyState onAdd={add} /> : <section className="exercise-list" aria-label="Exercises">
      {exercises.map((exercise) => <HomeExerciseCard key={exercise.id} exercise={exercise} open={open} addEntry={(id) => navigate({ name: "new-entry", exerciseId: id })} />)}
    </section>}
    <button className="primary-button floating-button" onClick={add}><span>+</span> New exercise</button>
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
      <button className="home-exercise-open" onClick={() => open(exercise.id)} aria-label={`Open ${exercise.name}`}>
        <span className="home-exercise-summary">
          <strong>{exercise.name}</strong>
          {latest ? <span className="home-exercise-last"><span>{formatSets(latest.reps)}</span><i>·</i><span>{relativeEntryTime(latest.created_at)}</span></span> : <span className="home-exercise-last is-empty">No results yet</span>}
        </span>
        <span className={`home-today-total ${exercise.stats.today_reps > 0 ? "has-reps" : ""}`}>
          <b>{exercise.stats.today_reps > 0 ? exercise.stats.today_reps.toLocaleString() : "—"}</b>
          <small>Today</small>
        </span>
      </button>
    </div>
    <div className="home-activity-row">
      <HomeActivityBars days={days} values={values} today={exercise.stats.today} />
      <button className="home-activity-add" onClick={() => addEntry(exercise.id)} aria-label={`Add result for ${exercise.name}`}><span aria-hidden="true">+</span></button>
    </div>
  </article>;
}

function HomeActivityBars({ days, values, today }: { days: string[]; values: number[]; today: string }) {
  const maximum = Math.max(...values, 1);
  return <div className="home-activity-bars" aria-label="Last seven days activity">
    {days.map((day, index) => {
      const value = values[index];
      const active = value > 0;
      const isToday = day === today;
      const label = new Intl.DateTimeFormat(undefined, { weekday: "narrow" }).format(new Date(`${day}T12:00:00`));
      return <span className={`home-activity-day ${active ? "has-activity" : ""} ${isToday ? "is-today" : ""}`} key={day}>
        <i style={{ height: `${active ? Math.max(3, (value / maximum) * 32) : 2}px` }} />
        <small>{label}</small>
      </span>;
    })}
  </div>;
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return <section className="empty-state"><div className="empty-orb">↗</div><h3>Your list is ready</h3><p>Add the first exercise you want to track.</p><button className="primary-button" onClick={onAdd}>Add your first exercise</button></section>;
}

function NewExercisePage({ back, done }: { back: () => void; done: () => void }) {
  const [name, setName] = useState(""); const [error, setError] = useState<string>(); const [saving, setSaving] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setSaving(true); setError(undefined); try { await api.createExercise(name.trim()); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create exercise."); } finally { setSaving(false); } };
  return <main className="app-shell"><Header title="New exercise" back={back} /><form className="screen-form new-exercise-form" onSubmit={submit}><label>Exercise name<input autoFocus value={name} onChange={(event) => setName(event.target.value)} placeholder="Exercise name" maxLength={255} /></label>{error && <ErrorNotice message={error} />}<button className="primary-button" disabled={!name.trim() || saving}>{saving ? "Creating…" : "Create exercise"}</button></form></main>;
}

function ExercisePage({ exerciseId, back, addEntry, settings, allWeeks, allResults, edit }: { exerciseId: number; back: () => void; addEntry: () => void; settings: () => void; allWeeks: () => void; allResults: () => void; edit: (entryId: number) => void }) {
  const [exercise, setExercise] = useState<Exercise>(); const [stats, setStats] = useState<ExerciseStats>(); const [entries, setEntries] = useState<ExerciseEntry[]>(); const [history, setHistory] = useState<HistoryDay[]>(); const [timezone, setTimezone] = useState<string>(); const [error, setError] = useState<string>();
  const [period, setPeriod] = useState<ChartPeriod>("7d");
  const load = useCallback(async () => { setError(undefined); try { const [all, nextStats, nextEntries, nextHistory, userSettings] = await Promise.all([api.exercises(), api.stats(exerciseId), api.entries(exerciseId), fetchAllHistory(exerciseId), api.settings()]); setExercise(all.find((item) => item.id === exerciseId)); setStats(nextStats); setEntries(nextEntries); setHistory(nextHistory); setTimezone(userSettings.timezone); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load the exercise."); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  if (error) return <main className="app-shell"><Header title="Exercise" back={back} /><ErrorNotice message={error} retry={load} /></main>;
  if (!exercise || !stats || !entries || !history || !timezone) return <main className="app-shell"><Header title="Exercise" back={back} /><Loading /></main>;
  return <main className="app-shell exercise-page">
    <Header title={exercise.name} back={back} action={<button className="icon-button settings-button" aria-label="Exercise settings" onClick={settings}><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="5" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="12" cy="19" r="1.5" /></svg></button>} />
    <section className="dashboard-card today-card">
      <div className="dashboard-label">Today</div>
      <div className="today-card-content">
        <div><strong>{stats.today_reps > 0 ? stats.today_reps.toLocaleString() : "—"}</strong><small>{stats.today_reps > 0 ? "reps" : "No results yet"}</small></div>
        {stats.last_entry && <div className="latest-result"><span>Latest</span><b>{formatSets(stats.last_entry.reps)}</b><small>{relativeEntryTime(stats.last_entry.created_at)}</small></div>}
      </div>
    </section>
    <button className="primary-button overview-add-button" onClick={addEntry}>+ Add result</button>
    <LastSevenDays days={history} today={stats.today} period={period} setPeriod={setPeriod} />
    <WeeklyProgress days={history} today={stats.today} onShowAll={allWeeks} />
    <section className="dashboard-card results-panel"><div className="section-heading"><h3>Recent results</h3></div>{entries.length === 0 ? <p className="muted">No results yet. Log your first set.</p> : <><RecentResults entries={entries.slice(0, 5)} timezone={timezone} onSelect={edit} /><div className="results-footer"><button className="text-button" onClick={allResults}>All results →</button></div></>}</section>
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

function formatMonth(value: Date) {
  return new Intl.DateTimeFormat(undefined, { month: "short", year: "2-digit" }).format(value);
}

function buildDailyActivity(days: HistoryDay[], today: string, count: number): ActivityDatum[] {
  const totals = new Map(days.map((day) => [day.date, day.total_reps]));
  const end = new Date(`${today}T12:00:00`);
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(end); date.setDate(date.getDate() - (count - index - 1));
    const dateString = isoDate(date);
    const label = count === 7
      ? new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(date)
      : new Intl.DateTimeFormat(undefined, { day: "numeric" }).format(date);
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

function LastSevenDays({ days, today, period, setPeriod }: { days: HistoryDay[]; today: string; period: ChartPeriod; setPeriod: (period: ChartPeriod) => void }) {
  const chartDays = period === "all" ? buildMonthlyActivity(days, today) : buildDailyActivity(days, today, period === "7d" ? 7 : 30);
  const [selectedKey, setSelectedKey] = useState<string>();
  const selected = chartDays.find((day) => day.key === selectedKey);
  const max = Math.max(...chartDays.map((day) => day.total), 1);
  const periodTotal = chartDays.reduce((sum, day) => sum + day.total, 0);
  const visibleAxis = period === "7d" ? new Set(chartDays.map((_, index) => index)) : axisIndexes(chartDays.length);
  return <section className="dashboard-card progress-card"><div className="progress-card-header"><div><div className="dashboard-label">Progress</div><div className="progress-period-total"><strong>{periodTotal.toLocaleString()}</strong><span>reps</span></div></div><div className="period-tabs">{(["7d", "30d", "all"] as ChartPeriod[]).map((item) => <button type="button" key={item} className={period === item ? "is-active" : ""} onClick={() => { setSelectedKey(undefined); setPeriod(item); }}>{item === "all" ? "All" : item}</button>)}</div></div><div className={`daily-bars activity-${period}`}>{chartDays.map((day, index) => <button type="button" className={`daily-bar ${day.total > 0 ? "has-activity" : ""} ${visibleAxis.has(index) ? "has-axis" : ""} ${selected?.key === day.key ? "is-selected" : ""}`} key={day.key} onClick={() => setSelectedKey(day.key)} aria-label={`${day.detail}: ${day.total.toLocaleString()} reps`} aria-pressed={selected?.key === day.key}>{period === "7d" && <strong>{day.total}</strong>}<div className="bar-track"><i style={{ height: day.total > 0 ? `${Math.max((day.total / max) * 100, 6)}%` : "2px" }} /></div>{visibleAxis.has(index) && <span>{day.label}</span>}</button>)}</div><p className="activity-detail" aria-live="polite">{selected && <>{selected.detail} <b>{selected.total.toLocaleString()} reps</b></>}</p></section>;
}

function WeeklyProgress({ days, today, onShowAll }: { days: HistoryDay[]; today: string; onShowAll: () => void }) {
  const weeks = buildWeeks(days, today, 5).slice(0, 5);
  const [current, previous] = weeks;
  const percent = previous.total > 0 ? Math.round(((current.total - previous.total) / previous.total) * 100) : null;
  const maximum = Math.max(...weeks.map((week) => week.total), 1);
  if (!days.length) return <section className="dashboard-card weekly-progress"><div className="section-heading"><h3>Weekly progress</h3><button className="text-button" onClick={onShowAll}>All weeks →</button></div><div className="chart-empty">Your weekly progress will appear after the first result.</div></section>;
  return <section className="dashboard-card weekly-progress"><div className="section-heading"><h3>Weekly progress</h3></div><div className="week-summary"><div className="week-summary-main"><span>{formatWeekRange(current.start, current.end)}</span><div className="week-summary-total"><strong>{current.total.toLocaleString()}</strong><small>reps</small></div></div>{percent !== null && <div className="week-summary-change"><strong className={percent >= 0 ? "positive" : "negative"}>{percent >= 0 ? "+" : ""}{percent}%</strong><span>vs last week</span></div>}</div><div className="week-list">{weeks.slice(1).map((week, index) => <WeekRow key={week.start} week={week} older={weeks[index + 2]} maximum={maximum} />)}</div><div className="week-footer"><div className="week-footer-stats"><div><small>Best</small><strong>{Math.max(...weeks.map((week) => week.total)).toLocaleString()}</strong></div><div><small>Avg</small><strong>{Math.round(weeks.reduce((sum, week) => sum + week.total, 0) / weeks.length).toLocaleString()}</strong></div></div><button className="text-button" onClick={onShowAll}>All weeks →</button></div></section>;
}

function formatWeekRange(start: string, end: string) {
  const startDate = new Date(`${start}T12:00:00`); const endDate = new Date(`${end}T12:00:00`);
  const month = new Intl.DateTimeFormat(undefined, { month: "short" });
  return startDate.getMonth() === endDate.getMonth() ? `${startDate.getDate()}–${endDate.getDate()} ${month.format(endDate)}` : `${startDate.getDate()} ${month.format(startDate)} – ${endDate.getDate()} ${month.format(endDate)}`;
}

function WeekRow({ week, older, maximum }: { week: Week; older?: Week; maximum: number }) {
  const change = older && older.total > 0 ? Math.round(((week.total - older.total) / older.total) * 100) : null;
  const barWidth = week.total > 0 ? Math.max(4, Math.round((week.total / maximum) * 100)) : 0;
  const changeLabel = change === null ? "—" : `${change >= 0 ? "+" : ""}${change}%`;
  return <div className="week-row"><div className="week-label"><strong>{formatWeekRange(week.start, week.end)}</strong></div><div className="week-bar" aria-hidden="true"><i style={{ width: `${barWidth}%` }} /></div><span className="week-total">{week.total.toLocaleString()}</span><b className={`week-change ${change === null ? "neutral" : change >= 0 ? "positive" : "negative"}`}>{changeLabel}</b></div>;
}

function RecentResults({ entries, timezone, onSelect }: { entries: ExerciseEntry[]; timezone: string; onSelect: (entryId: number) => void }) {
  const groups = entries.reduce<Array<{ date: string; entries: ExerciseEntry[] }>>((result, entry) => {
    const group = result.at(-1); if (group?.date === entry.performed_on) group.entries.push(entry); else result.push({ date: entry.performed_on, entries: [entry] }); return result;
  }, []);
  return <div className="result-list">{groups.map((group) => { const total = group.entries.reduce((sum, entry) => sum + totalReps(entry), 0); return <section className="result-day" key={group.date}><h4><span className="result-date">{formatDate(group.date)}</span><span className="result-day-total"><strong>{total.toLocaleString()}</strong> reps</span></h4>{group.entries.map((entry) => <button className="result-row result-button" key={entry.id} onClick={() => onSelect(entry.id)} aria-label={`Open result: ${formatSets(entry.reps)}, ${totalReps(entry).toLocaleString()} reps`}><div><strong>{formatSets(entry.reps)}</strong><small>{formatTime(entry.created_at, timezone)}</small></div><b>{totalReps(entry).toLocaleString()} <small>reps</small></b><span className="result-chevron" aria-hidden="true">›</span></button>)}</section>; })}</div>;
}

async function fetchAllEntries(exerciseId: number) {
  const entries: ExerciseEntry[] = [];
  for (let offset = 0; ; offset += 100) { const page = await api.entries(exerciseId, 100, offset); entries.push(...page); if (page.length < 100) return entries; }
}

async function fetchAllHistory(exerciseId: number) {
  const days: HistoryDay[] = [];
  for (let offset = 0; ; offset += 100) { const page = await api.history(exerciseId, 100, offset); days.push(...page); if (page.length < 100) return days; }
}

// Keep the frontend grammar aligned with bot.app.services.result_parser:
// `4x10` / `4×10`, numbers separated by spaces, commas, or plus signs.
function parseQuickResult(value: string): number[] {
  const text = value.trim();
  if (!text) throw new Error("Enter at least one set.");
  let parsed: number[];
  const repeated = text.match(/^(\d+)\s*[xX×*]\s*(\d+)$/);
  if (repeated) {
    const count = Number(repeated[1]); const reps = Number(repeated[2]);
    parsed = Array.from({ length: count }, () => reps);
  } else if (/^\d+(?:\s+\d+)*$/.test(text)) {
    parsed = text.split(/\s+/).map(Number);
  } else if (/^\d+(?:\s*[,+]\s*\d+)*$/.test(text)) {
    parsed = text.split(/\s*[,+]\s*/).map(Number);
  } else {
    throw new Error("Use formats such as 4×10, 10 10 10, or 10 + 10 + 8.");
  }
  if (!parsed.length || parsed.length > 100 || parsed.some((item) => !Number.isInteger(item) || item < 1 || item > 10000)) {
    throw new Error("Use 1–100 sets with 1–10,000 repetitions each.");
  }
  return parsed;
}

function WeeksPage({ exerciseId, back }: { exerciseId: number; back: () => void }) {
  const [days, setDays] = useState<HistoryDay[]>(); const [today, setToday] = useState<string>(); const [error, setError] = useState<string>();
  const load = useCallback(async () => { setError(undefined); try { const [history, settings] = await Promise.all([fetchAllHistory(exerciseId), api.settings()]); setDays(history); setToday(settings.today); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load weekly history."); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  if (!days || !today) return <main className="app-shell"><Header title="All weeks" back={back} />{error ? <ErrorNotice message={error} retry={load} /> : <Loading />}</main>;
  const weeks = buildWeeks(days, today);
  const maximum = Math.max(...weeks.map((week) => week.total), 1);
  return <main className="app-shell detail-list-page"><Header title="All weeks" back={back} />{!days.length ? <section className="dashboard-card"><div className="chart-empty">No weekly history yet.</div></section> : <section className="dashboard-card weekly-progress full-history"><div className="section-heading"><h3>Weekly history</h3><span>{weeks.length} weeks</span></div><div className="week-list">{weeks.map((week, index) => <WeekRow key={week.start} week={week} older={weeks[index + 1]} maximum={maximum} />)}</div></section>}</main>;
}

function ResultsPage({ exerciseId, back, edit }: { exerciseId: number; back: () => void; edit: (entryId: number) => void }) {
  const [entries, setEntries] = useState<ExerciseEntry[]>(); const [timezone, setTimezone] = useState<string>(); const [error, setError] = useState<string>();
  const load = useCallback(async () => { setError(undefined); try { const [allEntries, settings] = await Promise.all([fetchAllEntries(exerciseId), api.settings()]); setEntries(allEntries); setTimezone(settings.timezone); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load results."); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  if (!entries || !timezone) return <main className="app-shell"><Header title="All results" back={back} />{error ? <ErrorNotice message={error} retry={load} /> : <Loading />}</main>;
  return <main className="app-shell detail-list-page"><Header title="All results" back={back} /><section className="dashboard-card results-panel"><div className="section-heading"><h3>Training history</h3><span>{entries.length} results</span></div>{entries.length ? <RecentResults entries={entries} timezone={timezone} onSelect={edit} /> : <p className="muted">No results yet.</p>}</section></main>;
}

function EntryEditorPage({ exerciseId, entryId, back, done }: { exerciseId: number; entryId?: number; back: () => void; done: () => void }) {
  const isEditing = entryId !== undefined;
  const [reps, setReps] = useState<number[]>([10]); const [quickInput, setQuickInput] = useState("10"); const [quickError, setQuickError] = useState<string>(); const [date, setDate] = useState(""); const [today, setToday] = useState(""); const [exerciseName, setExerciseName] = useState(""); const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [error, setError] = useState<string>();
  const syncSets = (next: number[]) => { setReps(next); setQuickInput(formatSets(next)); setQuickError(undefined); };
  useEffect(() => { void (async () => { try { const [settings, exercises] = await Promise.all([api.settings(), api.exercises()]); const exercise = exercises.find((item) => item.id === exerciseId); if (!exercise) throw new Error("Exercise not found."); setToday(settings.today); setExerciseName(exercise.name); if (entryId === undefined) { setDate(settings.today); } else { const entry = (await fetchAllEntries(exerciseId)).find((item) => item.id === entryId); if (!entry) throw new Error("Result not found."); syncSets(entry.reps); setDate(entry.performed_on); } } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load result."); } finally { setLoading(false); } })(); }, [entryId, exerciseId]);
  const updateSet = (index: number, value: number) => syncSets(reps.map((setReps, itemIndex) => itemIndex === index ? value : setReps));
  const applyQuickInput = (value: string) => { setQuickInput(value); try { const next = parseQuickResult(value); setReps(next); setQuickError(undefined); } catch { setQuickError(undefined); } };
  const validateQuickInput = () => { try { const next = parseQuickResult(quickInput); syncSets(next); return next; } catch (reason) { setQuickError(reason instanceof Error ? reason.message : "Invalid result format."); return undefined; } };
  const save = async (event: FormEvent) => { event.preventDefault(); const parsed = validateQuickInput(); if (!date || !parsed) return; setSaving(true); setError(undefined); try { if (entryId === undefined) await api.createEntry(exerciseId, parsed, date); else await api.updateEntry(entryId, parsed, date); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save result."); } finally { setSaving(false); } };
  const remove = async () => { if (!entryId || !window.confirm("Delete this result? This cannot be undone.")) return; setSaving(true); try { await api.deleteEntry(entryId); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not delete result."); setSaving(false); } };
  const total = reps.reduce((sum, value) => sum + (Number.isFinite(value) ? value : 0), 0);
  if (loading) return <main className="app-shell"><Header title={isEditing ? "Edit result" : "Add result"} back={back} /><Loading /></main>;
  if (error && !date) return <main className="app-shell"><Header title={isEditing ? "Edit result" : "Add result"} back={back} /><ErrorNotice message={error} /></main>;
  return <main className="app-shell"><Header title={isEditing ? "Edit result" : "Add result"} back={back} /><p className="entry-exercise-context" title={exerciseName}>{exerciseName}</p><form className="entry-editor" onSubmit={save}><label className="quick-entry"><span>Quick entry</span><input value={quickInput} onChange={(event) => applyQuickInput(event.target.value)} onBlur={validateQuickInput} placeholder="4×10 or 10 + 10 + 8" autoComplete="off" /><small>Try 4×10, 10 10 10, or 10 + 10 + 8.</small></label>{quickError && <p className="quick-error">{quickError}</p>}<label className="date-picker"><span>Date</span><input id="entry-date" type="date" value={date} max={today} onChange={(event) => setDate(event.target.value)} /><small>{date === today ? "Today" : "Selected training date"}</small></label><section className="sets-panel"><div className="section-heading"><h3>Sets</h3><span>{total.toLocaleString()} reps total</span></div><div className="set-list">{reps.map((value, index) => <div className="set-editor" key={index}><span>Set {index + 1}</span><button type="button" aria-label={`Decrease set ${index + 1}`} onClick={() => updateSet(index, Math.max(1, value - 1))}>−</button><input aria-label={`Repetitions for set ${index + 1}`} type="number" inputMode="numeric" min="1" max="10000" value={value || ""} onChange={(event) => updateSet(index, Number(event.target.value))} /><button type="button" aria-label={`Increase set ${index + 1}`} onClick={() => updateSet(index, Math.min(10000, value + 1))}>+</button><button className="remove-set" type="button" aria-label={`Remove set ${index + 1}`} disabled={reps.length === 1} onClick={() => syncSets(reps.filter((_, itemIndex) => itemIndex !== index))}>×</button></div>)}</div><button className="add-set" type="button" onClick={() => syncSets([...reps, reps.at(-1) ?? 10])}>＋ Add set</button></section>{error && <ErrorNotice message={error} />}<button className="primary-button" disabled={saving}>{saving ? "Saving…" : isEditing ? "Save changes" : "Save result"}</button>{isEditing && <button className="danger-button editor-delete" type="button" disabled={saving} onClick={remove}>Delete result</button>}</form></main>;
}

function ExerciseSettingsPage({ exerciseId, back, home }: { exerciseId: number; back: () => void; home: () => void }) {
  const [exercise, setExercise] = useState<Exercise>(); const [name, setName] = useState(""); const [error, setError] = useState<string>(); const [saving, setSaving] = useState(false);
  const load = useCallback(async () => { try { const item = (await api.exercises()).find((candidate) => candidate.id === exerciseId); if (!item) throw new Error("Exercise not found."); setExercise(item); setName(item.name); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load settings."); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  const saveName = async (event: FormEvent) => { event.preventDefault(); setSaving(true); setError(undefined); try { const updated = await api.updateExercise(exerciseId, name.trim()); setExercise(updated); setName(updated.name); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save the name."); } finally { setSaving(false); } };
  const toggleReport = async () => { if (!exercise) return; setSaving(true); setError(undefined); try { setExercise(await api.updateWeeklyReport(exerciseId, !exercise.weekly_report_enabled)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not update report setting."); } finally { setSaving(false); } };
  const archive = async () => { if (!window.confirm("Archive this exercise? Its results will stay saved.")) return; try { await api.archiveExercise(exerciseId); home(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not archive the exercise."); } };
  if (!exercise) return <main className="app-shell"><Header title="Exercise settings" back={back} />{error ? <ErrorNotice message={error} retry={load} /> : <Loading />}</main>;
  return <main className="app-shell"><Header title="Exercise settings" back={back} /><form className="screen-form settings-form" onSubmit={saveName}><label>Exercise name<input value={name} onChange={(event) => setName(event.target.value)} maxLength={255} /></label><button className="secondary-button" disabled={!name.trim() || saving}>{saving ? "Saving…" : "Save name"}</button></form><section className="settings-group"><div><strong>Weekly report</strong><p>Include this exercise in the weekly summary.</p></div><button className={`switch ${exercise.weekly_report_enabled ? "is-on" : ""}`} aria-label="Toggle weekly report" onClick={toggleReport} disabled={saving}><span /></button></section>{error && <ErrorNotice message={error} />}<section className="danger-zone"><h3>Danger zone</h3><p>Archiving hides this exercise from your list. You can restore it later from the bot.</p><button className="danger-button" onClick={archive}>Archive exercise</button></section></main>;
}

function SettingsPage({ back }: { back: () => void }) {
  const [settings, setSettings] = useState<Settings>(); const [timezone, setTimezone] = useState(""); const [language, setLanguage] = useState<Settings["language"]>("en"); const [error, setError] = useState<string>(); const [saving, setSaving] = useState(false);
  const load = useCallback(async () => { try { const response = await api.settings(); setSettings(response); setTimezone(response.timezone); setLanguage(response.language); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load settings."); } }, []);
  useEffect(() => { void load(); }, [load]);
  const save = async (event: FormEvent) => { event.preventDefault(); setSaving(true); setError(undefined); try { setSettings(await api.updateSettings({ timezone: timezone.trim(), language })); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save settings."); } finally { setSaving(false); } };
  if (!settings) return <main className="app-shell"><Header title="Settings" back={back} />{error ? <ErrorNotice message={error} retry={load} /> : <Loading />}</main>;
  const hasCurrentTimezone = timezoneOptions.some(([value]) => value === timezone);
  return <main className="app-shell"><Header title="Settings" back={back} /><form className="screen-form settings-form" onSubmit={save}><p className="eyebrow">PREFERENCES</p><label>Time zone<select value={timezone} onChange={(event) => setTimezone(event.target.value)}>{!hasCurrentTimezone && <option value={timezone}>{timezone}</option>}{timezoneOptions.map(([value, label]) => <option key={value} value={value}>{label} — {value}</option>)}</select><small>Uses the same curated timezone choices as the Telegram bot.</small></label><label>Language<select value={language} onChange={(event) => setLanguage(event.target.value as Settings["language"])}>{languageOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>{error && <ErrorNotice message={error} />}<button className="primary-button" disabled={!timezone.trim() || saving}>{saving ? "Saving…" : "Save settings"}</button></form><p className="local-note">This first web version uses a local development identity. Telegram account verification will replace it in a later step.</p></main>;
}

export default App;
