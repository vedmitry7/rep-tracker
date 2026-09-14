import { FormEvent, useCallback, useEffect, useState } from "react";
import { api } from "./api";
import repkaLogo from "./assets/repka-logo.png";
import type { Exercise, ExerciseEntry, ExerciseStats, HistoryDay, Settings } from "./types";

type Route = "home" | "new-exercise" | "exercise" | "new-entry" | "exercise-settings" | "settings" | "weeks" | "results" | "edit-entry";

type AppRoute = { name: Route; exerciseId?: number; entryId?: number };
type ExerciseSummary = Exercise & { stats: ExerciseStats };

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

function Header({ title, back, action }: { title: string; back?: () => void; action?: React.ReactNode }) {
  return <header className="topbar">
    {back ? <button className="icon-button" aria-label="Go back" onClick={back}>‹</button> : <span className="brand-mark">R</span>}
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
      setExercises(await Promise.all(activeExercises.map(async (exercise) => ({ ...exercise, stats: await api.stats(exercise.id) }))));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load exercises."); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return <main className="app-shell">
    <header className="topbar home-topbar"><div className="home-brand"><img src={repkaLogo} alt="" /><h1>Repka</h1></div><button className="icon-button" aria-label="Global settings" onClick={settings}>⚙</button></header>
    {error ? <ErrorNotice message={error} retry={load} /> : !exercises ? <Loading /> : exercises.length === 0 ? <EmptyState onAdd={add} /> : <section className="exercise-list">
      {exercises.map((exercise) => <button className="exercise-card" key={exercise.id} onClick={() => open(exercise.id)}>
        <span className="exercise-card-copy"><strong>{exercise.name}</strong><span className="exercise-metrics"><span><small>Today</small><b>{exercise.stats.today_reps.toLocaleString()}</b></span><span><small>Last</small><b>{exercise.stats.last_entry ? formatSets(exercise.stats.last_entry.reps) : "No results yet"}</b></span><span><small>7 days</small><b>{exercise.stats.last_7_days_reps.toLocaleString()}</b></span></span></span><span className="chevron">›</span>
      </button>)}
    </section>}
    <button className="primary-button floating-button" onClick={add}><span>＋</span> Add exercise</button>
  </main>;
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return <section className="empty-state"><div className="empty-orb">↗</div><h3>Your list is ready</h3><p>Add the first exercise you want to track.</p><button className="primary-button" onClick={onAdd}>Add your first exercise</button></section>;
}

function NewExercisePage({ back, done }: { back: () => void; done: () => void }) {
  const [name, setName] = useState(""); const [error, setError] = useState<string>(); const [saving, setSaving] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setSaving(true); setError(undefined); try { await api.createExercise(name.trim()); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create exercise."); } finally { setSaving(false); } };
  return <main className="app-shell"><Header title="New exercise" back={back} /><form className="screen-form" onSubmit={submit}><div className="intro compact"><p className="eyebrow">YOUR PROGRAM</p><h2>What are you training?</h2><p>You can rename it any time.</p></div><label>Exercise name<input autoFocus value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Push-ups" maxLength={255} /></label>{error && <ErrorNotice message={error} />}<button className="primary-button" disabled={!name.trim() || saving}>{saving ? "Creating…" : "Create exercise"}</button></form></main>;
}

function ExercisePage({ exerciseId, back, addEntry, settings, allWeeks, allResults, edit }: { exerciseId: number; back: () => void; addEntry: () => void; settings: () => void; allWeeks: () => void; allResults: () => void; edit: (entryId: number) => void }) {
  const [exercise, setExercise] = useState<Exercise>(); const [stats, setStats] = useState<ExerciseStats>(); const [entries, setEntries] = useState<ExerciseEntry[]>(); const [history, setHistory] = useState<HistoryDay[]>(); const [timezone, setTimezone] = useState<string>(); const [error, setError] = useState<string>(); const [menuOpen, setMenuOpen] = useState(false);
  const load = useCallback(async () => { setError(undefined); try { const [all, nextStats, nextEntries, nextHistory, userSettings] = await Promise.all([api.exercises(), api.stats(exerciseId), api.entries(exerciseId), api.history(exerciseId), api.settings()]); setExercise(all.find((item) => item.id === exerciseId)); setStats(nextStats); setEntries(nextEntries); setHistory(nextHistory); setTimezone(userSettings.timezone); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load the exercise."); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  if (error) return <main className="app-shell"><Header title="Exercise" back={back} /><ErrorNotice message={error} retry={load} /></main>;
  if (!exercise || !stats || !entries || !history || !timezone) return <main className="app-shell"><Header title="Exercise" back={back} /><Loading /></main>;
  return <main className="app-shell">
    <Header title={exercise.name} back={back} action={<div className="menu-wrap"><button className="icon-button menu-button" aria-label="Exercise menu" aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}>⋮</button>{menuOpen && <div className="exercise-menu"><button onClick={settings}>Exercise settings</button></div>}</div>} />
    <section className="exercise-overview"><div className="today-hero"><div className="today-primary"><p>TODAY</p><strong>{stats.today_reps.toLocaleString()} <small>reps</small></strong></div><div className="today-details"><CompactMetric label="7 days" value={stats.last_7_days_reps} /><CompactMetric label="30 days" value={stats.last_30_days_reps} /><CompactMetric label="All time" value={stats.total_reps} /></div><div className="card-last-result"><p>LAST RESULT</p>{stats.last_entry ? <strong>{formatSets(stats.last_entry.reps)} <span>· {formatResultMoment(stats.last_entry, stats.today, timezone)}</span></strong> : <span>No results yet</span>}</div></div><button className="primary-button overview-add-button" onClick={addEntry}><span>＋</span> Add result</button></section>
    <LastSevenDays days={history} today={stats.today} />
    <WeeklyProgress days={history} today={stats.today} onShowAll={allWeeks} />
    <section className="panel results-panel"><div className="section-heading"><h3>Recent results</h3><button className="text-button" onClick={allResults}>All results</button></div>{entries.length === 0 ? <p className="muted">No results yet. Log your first set.</p> : <RecentResults entries={entries.slice(0, 5)} timezone={timezone} onSelect={edit} />}</section>
  </main>;
}

function CompactMetric({ label, value }: { label: string; value: number }) { return <div className="compact-metric"><small>{label}</small><strong>{value.toLocaleString()}</strong></div>; }

type Week = { start: string; end: string; total: number };

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

function LastSevenDays({ days, today }: { days: HistoryDay[]; today: string }) {
  const totals = new Map(days.map((day) => [day.date, day.total_reps]));
  const end = new Date(`${today}T12:00:00`);
  const chartDays = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(end); date.setDate(date.getDate() - (6 - index));
    const dateString = isoDate(date);
    return { date: dateString, label: new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(date), total: totals.get(dateString) ?? 0, isToday: dateString === today };
  });
  const max = Math.max(...chartDays.map((day) => day.total), 1);
  return <section className="seven-days"><div className="section-heading"><h3>Last 7 days</h3></div><div className="daily-bars">{chartDays.map((day) => <div className={`daily-bar ${day.total > 0 ? "has-activity" : ""} ${day.isToday ? "is-today" : ""}`} key={day.date}><strong>{day.total}</strong><div className="bar-track">{day.total > 0 && <i style={{ height: `${Math.max((day.total / max) * 100, 9)}%` }} />}</div><span>{day.label}</span></div>)}</div></section>;
}

function WeeklyProgress({ days, today, onShowAll }: { days: HistoryDay[]; today: string; onShowAll: () => void }) {
  const weeks = buildWeeks(days, today, 4).slice(0, 4);
  const [current, previous] = weeks;
  const delta = current.total - previous.total;
  const percent = previous.total > 0 ? Math.round((delta / previous.total) * 100) : null;
  const max = Math.max(...weeks.map((week) => week.total), 1);
  if (!days.length) return <section className="panel"><div className="section-heading"><h3>Weekly progress</h3><button className="text-button" onClick={onShowAll}>All weeks</button></div><div className="chart-empty">Your weekly progress will appear after the first result.</div></section>;
  return <section className="weekly-progress"><div className="section-heading"><h3>Weekly progress</h3><button className="text-button" onClick={onShowAll}>All weeks</button></div><div className="week-hero"><div className="week-hero-total"><p>THIS WEEK</p><strong>{current.total.toLocaleString()} <small>reps</small></strong></div>{previous.total === 0 ? <div className="week-comparison neutral"><strong>First tracked week</strong></div> : <div className={`week-comparison ${delta >= 0 ? "positive" : "negative"}`}><strong>{delta >= 0 ? "↑" : "↓"} {Math.abs(delta).toLocaleString()} <small>reps</small> {percent !== null && `(${delta >= 0 ? "+" : ""}${percent}%)`}</strong><span>vs last week</span></div>}</div><div className="week-list">{weeks.slice(1).map((week, index) => <WeekRow key={week.start} week={week} older={weeks[index + 2]} current={false} max={max} />)}</div><div className="week-footer"><div><small>Best week</small><strong>{Math.max(...weeks.map((week) => week.total)).toLocaleString()} reps</strong></div><div><small>Average</small><strong>{Math.round(weeks.reduce((sum, week) => sum + week.total, 0) / weeks.length).toLocaleString()} reps</strong></div></div></section>;
}

function WeekRow({ week, older, current, max }: { week: Week; older?: Week; current: boolean; max: number }) {
  const change = older && older.total > 0 ? Math.round(((week.total - older.total) / older.total) * 100) : null;
  return <div className={`week-row ${current ? "current" : ""}`}><div className="week-label"><strong>{current ? "Current week" : `${formatDate(week.start)} – ${formatDate(week.end)}`}</strong><span>{week.total.toLocaleString()} reps</span></div><div className="week-bar"><i style={{ width: `${(week.total / max) * 100}%` }} /></div><b className={change === null ? "neutral" : change >= 0 ? "positive" : "negative"}>{change === null ? "—" : `${change >= 0 ? "+" : ""}${change}%`}</b></div>;
}

function RecentResults({ entries, timezone, onSelect }: { entries: ExerciseEntry[]; timezone: string; onSelect: (entryId: number) => void }) {
  const groups = entries.reduce<Array<{ date: string; entries: ExerciseEntry[] }>>((result, entry) => {
    const group = result.at(-1); if (group?.date === entry.performed_on) group.entries.push(entry); else result.push({ date: entry.performed_on, entries: [entry] }); return result;
  }, []);
  return <div className="result-list">{groups.map((group) => <section className="result-day" key={group.date}><h4>{formatDate(group.date)} <span>{group.entries.reduce((sum, entry) => sum + totalReps(entry), 0)} reps</span></h4>{group.entries.map((entry) => <button className="result-row result-button" key={entry.id} onClick={() => onSelect(entry.id)}><div><strong>{entry.reps.join(" + ")}</strong><small>Added at {formatTime(entry.created_at, timezone)}</small></div><b>{totalReps(entry)} <small>reps</small></b><span className="result-chevron">›</span></button>)}</section>)}</div>;
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
  const weeks = buildWeeks(days, today); const max = Math.max(...weeks.map((week) => week.total), 1);
  return <main className="app-shell"><Header title="All weeks" back={back} />{!days.length ? <section className="panel"><div className="chart-empty">No weekly history yet.</div></section> : <section className="weekly-progress full-history"><div className="section-heading"><h3>Weekly history</h3><span>{weeks.length} weeks</span></div><div className="week-list">{weeks.map((week, index) => <WeekRow key={week.start} week={week} older={weeks[index + 1]} current={index === 0} max={max} />)}</div></section>}</main>;
}

function ResultsPage({ exerciseId, back, edit }: { exerciseId: number; back: () => void; edit: (entryId: number) => void }) {
  const [entries, setEntries] = useState<ExerciseEntry[]>(); const [timezone, setTimezone] = useState<string>(); const [error, setError] = useState<string>();
  const load = useCallback(async () => { setError(undefined); try { const [allEntries, settings] = await Promise.all([fetchAllEntries(exerciseId), api.settings()]); setEntries(allEntries); setTimezone(settings.timezone); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load results."); } }, [exerciseId]);
  useEffect(() => { void load(); }, [load]);
  if (!entries || !timezone) return <main className="app-shell"><Header title="All results" back={back} />{error ? <ErrorNotice message={error} retry={load} /> : <Loading />}</main>;
  return <main className="app-shell"><Header title="All results" back={back} /><section className="panel results-panel"><div className="section-heading"><h3>Training history</h3><span>{entries.length} results</span></div>{entries.length ? <RecentResults entries={entries} timezone={timezone} onSelect={edit} /> : <p className="muted">No results yet.</p>}</section></main>;
}

function EntryEditorPage({ exerciseId, entryId, back, done }: { exerciseId: number; entryId?: number; back: () => void; done: () => void }) {
  const isEditing = entryId !== undefined;
  const [reps, setReps] = useState<number[]>([10]); const [quickInput, setQuickInput] = useState("10"); const [quickError, setQuickError] = useState<string>(); const [date, setDate] = useState(""); const [today, setToday] = useState(""); const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [error, setError] = useState<string>();
  const syncSets = (next: number[]) => { setReps(next); setQuickInput(formatSets(next)); setQuickError(undefined); };
  useEffect(() => { void (async () => { try { const settings = await api.settings(); setToday(settings.today); if (entryId === undefined) { setDate(settings.today); } else { const entry = (await fetchAllEntries(exerciseId)).find((item) => item.id === entryId); if (!entry) throw new Error("Result not found."); syncSets(entry.reps); setDate(entry.performed_on); } } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load result."); } finally { setLoading(false); } })(); }, [entryId, exerciseId]);
  const updateSet = (index: number, value: number) => syncSets(reps.map((setReps, itemIndex) => itemIndex === index ? value : setReps));
  const applyQuickInput = (value: string) => { setQuickInput(value); try { const next = parseQuickResult(value); setReps(next); setQuickError(undefined); } catch { setQuickError(undefined); } };
  const validateQuickInput = () => { try { const next = parseQuickResult(quickInput); syncSets(next); return next; } catch (reason) { setQuickError(reason instanceof Error ? reason.message : "Invalid result format."); return undefined; } };
  const save = async (event: FormEvent) => { event.preventDefault(); const parsed = validateQuickInput(); if (!date || !parsed) return; setSaving(true); setError(undefined); try { if (entryId === undefined) await api.createEntry(exerciseId, parsed, date); else await api.updateEntry(entryId, parsed, date); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save result."); } finally { setSaving(false); } };
  const remove = async () => { if (!entryId || !window.confirm("Delete this result? This cannot be undone.")) return; setSaving(true); try { await api.deleteEntry(entryId); done(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not delete result."); setSaving(false); } };
  const total = reps.reduce((sum, value) => sum + (Number.isFinite(value) ? value : 0), 0);
  if (loading) return <main className="app-shell"><Header title={isEditing ? "Edit result" : "Add result"} back={back} /><Loading /></main>;
  if (error && !date) return <main className="app-shell"><Header title={isEditing ? "Edit result" : "Add result"} back={back} /><ErrorNotice message={error} /></main>;
  return <main className="app-shell"><Header title={isEditing ? "Edit result" : "Add result"} back={back} /><form className="entry-editor" onSubmit={save}><label className="quick-entry"><span>Quick entry</span><input value={quickInput} onChange={(event) => applyQuickInput(event.target.value)} onBlur={validateQuickInput} placeholder="4×10 or 10 + 10 + 8" autoComplete="off" /><small>Try 4×10, 10 10 10, or 10 + 10 + 8.</small></label>{quickError && <p className="quick-error">{quickError}</p>}<label className="date-picker"><span>Date</span><input id="entry-date" type="date" value={date} max={today} onChange={(event) => setDate(event.target.value)} /><small>{date === today ? "Today" : "Selected training date"}</small></label><section className="sets-panel"><div className="section-heading"><h3>Sets</h3><span>{total.toLocaleString()} reps total</span></div><div className="set-list">{reps.map((value, index) => <div className="set-editor" key={index}><span>Set {index + 1}</span><button type="button" aria-label={`Decrease set ${index + 1}`} onClick={() => updateSet(index, Math.max(1, value - 1))}>−</button><input aria-label={`Repetitions for set ${index + 1}`} type="number" inputMode="numeric" min="1" max="10000" value={value || ""} onChange={(event) => updateSet(index, Number(event.target.value))} /><button type="button" aria-label={`Increase set ${index + 1}`} onClick={() => updateSet(index, Math.min(10000, value + 1))}>+</button><button className="remove-set" type="button" aria-label={`Remove set ${index + 1}`} disabled={reps.length === 1} onClick={() => syncSets(reps.filter((_, itemIndex) => itemIndex !== index))}>×</button></div>)}</div><button className="add-set" type="button" onClick={() => syncSets([...reps, reps.at(-1) ?? 10])}>＋ Add set</button></section>{error && <ErrorNotice message={error} />}<button className="primary-button" disabled={saving}>{saving ? "Saving…" : isEditing ? "Save changes" : "Save result"}</button>{isEditing && <button className="danger-button editor-delete" type="button" disabled={saving} onClick={remove}>Delete result</button>}</form></main>;
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
