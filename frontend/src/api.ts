import type { Exercise, ExerciseEntry, ExerciseStats, HistoryDay, Identity, Settings } from "./types";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
export const identity: Identity = {
  provider: import.meta.env.VITE_DEV_PROVIDER ?? "web-dev",
  external_id: import.meta.env.VITE_DEV_EXTERNAL_ID ?? "local-user",
};

type QueryValue = string | number | boolean | undefined;

async function request<T>(path: string, options: RequestInit = {}, query?: Record<string, QueryValue>): Promise<T> {
  const url = new URL(`${baseUrl}${path}`, window.location.origin);
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined) url.searchParams.set(key, String(value));
  });
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed (${response.status})`);
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

const ownedQuery = () => identity;
const ownedBody = <T extends object>(payload: T) => ({ ...identity, ...payload });

export const api = {
  resolveUser: () => request("/users/resolve", {
    method: "POST",
    body: JSON.stringify(ownedBody({
      default_timezone: import.meta.env.VITE_DEV_TIMEZONE ?? Intl.DateTimeFormat().resolvedOptions().timeZone ?? "Europe/Moscow",
      default_language: import.meta.env.VITE_DEV_LANGUAGE ?? "en",
    })),
  }),
  exercises: () => request<Exercise[]>("/exercises", {}, ownedQuery()),
  createExercise: (name: string) => request<Exercise>("/exercises", { method: "POST", body: JSON.stringify(ownedBody({ name })) }),
  updateExercise: (id: number, name: string) => request<Exercise>(`/exercises/${id}`, { method: "PATCH", body: JSON.stringify(ownedBody({ name })) }),
  updateWeeklyReport: (id: number, weekly_report_enabled: boolean) => request<Exercise>(`/exercises/${id}/weekly-report`, { method: "PATCH", body: JSON.stringify(ownedBody({ weekly_report_enabled })) }),
  archiveExercise: (id: number) => request<void>(`/exercises/${id}`, { method: "DELETE" }, ownedQuery()),
  stats: (id: number) => request<ExerciseStats>(`/exercises/${id}/stats`, {}, ownedQuery()),
  entries: (id: number, limit = 20, offset = 0) => request<ExerciseEntry[]>(`/exercises/${id}/entries`, {}, { ...ownedQuery(), limit, offset }),
  history: (id: number, limit = 100, offset = 0) => request<HistoryDay[]>(`/exercises/${id}/history-days`, {}, { ...ownedQuery(), limit, offset }),
  createEntry: (exercise_id: number, reps: number[], performed_on: string) => request<ExerciseEntry>("/exercise-entries", { method: "POST", body: JSON.stringify(ownedBody({ exercise_id, reps, performed_on })) }),
  updateEntry: (id: number, reps: number[], performed_on: string) => request<ExerciseEntry>(`/exercise-entries/${id}`, { method: "PATCH", body: JSON.stringify(ownedBody({ reps, performed_on })) }),
  deleteEntry: (id: number) => request<void>(`/exercise-entries/${id}`, { method: "DELETE" }, ownedQuery()),
  settings: () => request<Settings>("/users/settings", {}, ownedQuery()),
  updateSettings: (settings: Partial<Pick<Settings, "timezone" | "language">>) => request<Settings>("/users/settings", { method: "PATCH", body: JSON.stringify(ownedBody(settings)) }),
};
