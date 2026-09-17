import type { Exercise, ExerciseEntry, ExerciseStats, HistoryDay, Settings } from "./types";
import { getTelegramInitData } from "./telegram";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/mini-app";
const requestFailureMessage = "Unable to load data. Please try again.";
const requestTimeoutMessage = "The connection timed out. Please try again.";
const requestTimeoutMs = 15_000;

type QueryValue = string | number | boolean | undefined;

async function request<T>(path: string, options: RequestInit = {}, query?: Record<string, QueryValue>): Promise<T> {
  const url = new URL(`${baseUrl}${path}`, window.location.origin);
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined) url.searchParams.set(key, String(value));
  });
  const abortController = new AbortController();
  const timeoutId = window.setTimeout(() => abortController.abort(), requestTimeoutMs);
  try {
    const response = await fetch(url, {
      ...options,
      signal: abortController.signal,
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": getTelegramInitData(),
        ...options.headers,
      },
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => null) as { detail?: string } | null;
      console.error("Mini App request failed", {
        method: options.method ?? "GET",
        path: url.pathname,
        status: response.status,
        detail: payload?.detail,
      });
      throw new Error(requestFailureMessage);
    }
    return response.status === 204 ? undefined as T : response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof Error && error.message === requestFailureMessage) throw error;
    console.error("Mini App request could not be completed", {
      method: options.method ?? "GET",
      path: url.pathname,
      error,
    });
    throw new Error(requestFailureMessage);
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export const api = {
  resolveUser: () => request("/users/resolve", {
    method: "POST",
    body: JSON.stringify({
      default_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone ?? "Europe/Moscow",
    }),
  }),
  exercises: () => request<Exercise[]>("/exercises"),
  createExercise: (name: string) => request<Exercise>("/exercises", { method: "POST", body: JSON.stringify({ name }) }),
  updateExercise: (id: number, name: string) => request<Exercise>(`/exercises/${id}`, { method: "PATCH", body: JSON.stringify({ name }) }),
  updateWeeklyReport: (id: number, weekly_report_enabled: boolean) => request<Exercise>(`/exercises/${id}/weekly-report`, { method: "PATCH", body: JSON.stringify({ weekly_report_enabled }) }),
  archiveExercise: (id: number) => request<void>(`/exercises/${id}`, { method: "DELETE" }),
  stats: (id: number) => request<ExerciseStats>(`/exercises/${id}/stats`),
  entries: (id: number, limit = 20, offset = 0) => request<ExerciseEntry[]>(`/exercises/${id}/entries`, {}, { limit, offset }),
  entriesForDay: (id: number, date: string, limit = 100, offset = 0) => request<ExerciseEntry[]>(`/exercises/${id}/entries`, {}, { from: date, to: date, limit, offset }),
  history: (id: number, limit = 100, offset = 0) => request<HistoryDay[]>(`/exercises/${id}/history-days`, {}, { limit, offset }),
  createEntry: (exercise_id: number, reps: number[], performed_on: string) => request<ExerciseEntry>("/exercise-entries", { method: "POST", body: JSON.stringify({ exercise_id, reps, performed_on }) }),
  updateEntry: (id: number, reps: number[], performed_on: string) => request<ExerciseEntry>(`/exercise-entries/${id}`, { method: "PATCH", body: JSON.stringify({ reps, performed_on }) }),
  deleteEntry: (id: number) => request<void>(`/exercise-entries/${id}`, { method: "DELETE" }),
  settings: () => request<Settings>("/users/settings"),
  updateSettings: (settings: Partial<Pick<Settings, "timezone" | "language">>) => request<Settings>("/users/settings", { method: "PATCH", body: JSON.stringify(settings) }),
};
