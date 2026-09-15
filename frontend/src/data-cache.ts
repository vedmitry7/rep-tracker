import { api } from "./api";
import type { Exercise, ExerciseEntry, ExerciseStats, HistoryDay, Settings } from "./types";

export type ExerciseSummary = Exercise & { stats: ExerciseStats; history: HistoryDay[] };
export type ExerciseDetail = {
  exercise: Exercise;
  stats: ExerciseStats;
  history: HistoryDay[];
  timezone: string;
};
export type ResultsHistory = { days: HistoryDay[]; hasMore: boolean };

type CacheSlot<T> = { value?: T; updatedAt: number; pending?: Promise<T> };

const DASHBOARD_TTL = 30_000;
const DETAIL_TTL = 30_000;
const SETTINGS_TTL = 5 * 60_000;
const FULL_HISTORY_TTL = 5 * 60_000;

async function fetchAll<T>(fetchPage: (limit: number, offset: number) => Promise<T[]>) {
  const result: T[] = [];
  for (let offset = 0; ; offset += 100) {
    const page = await fetchPage(100, offset);
    result.push(...page);
    if (page.length < 100) return result;
  }
}

class AppDataCache {
  private resolvedUser?: Promise<unknown>;
  private exercises: CacheSlot<Exercise[]> = { updatedAt: 0 };
  private dashboard: CacheSlot<ExerciseSummary[]> = { updatedAt: 0 };
  private settings: CacheSlot<Settings> = { updatedAt: 0 };
  private details = new Map<number, CacheSlot<ExerciseDetail>>();
  private fullHistories = new Map<number, CacheSlot<HistoryDay[]>>();
  private fullEntries = new Map<number, CacheSlot<ExerciseEntry[]>>();
  private entriesByDay = new Map<string, CacheSlot<ExerciseEntry[]>>();
  private resultsHistories = new Map<number, CacheSlot<ResultsHistory>>();

  resolveUser() {
    if (!this.resolvedUser) {
      this.resolvedUser = api.resolveUser().catch((error) => {
        this.resolvedUser = undefined;
        throw error;
      });
    }
    return this.resolvedUser;
  }

  peekDashboard() { return this.dashboard.value; }
  peekDetail(exerciseId: number) { return this.details.get(exerciseId)?.value; }
  peekFullHistory(exerciseId: number) { return this.fullHistories.get(exerciseId)?.value; }
  peekFullEntries(exerciseId: number) { return this.fullEntries.get(exerciseId)?.value; }
  peekResultsHistory(exerciseId: number) { return this.resultsHistories.get(exerciseId)?.value; }
  peekSettings() { return this.settings.value; }
  peekEntry(exerciseId: number, entryId: number) {
    for (const [key, slot] of this.entriesByDay) {
      if (!key.startsWith(`${exerciseId}:`)) continue;
      const entry = slot.value?.find((item) => item.id === entryId);
      if (entry) return entry;
    }
    return this.fullEntries.get(exerciseId)?.value?.find((item) => item.id === entryId);
  }
  peekExercise(exerciseId: number) {
    return this.details.get(exerciseId)?.value?.exercise
      ?? this.exercises.value?.find((exercise) => exercise.id === exerciseId)
      ?? this.dashboard.value?.find((exercise) => exercise.id === exerciseId);
  }

  async loadDashboard(force = false) {
    return this.load(this.dashboard, DASHBOARD_TTL, force, async () => {
      const activeExercises = await this.loadExercises(force);
      return Promise.all(activeExercises.map(async (exercise) => {
        const [stats, history] = await Promise.all([api.stats(exercise.id), api.history(exercise.id, 7)]);
        return { ...exercise, stats, history };
      }));
    });
  }

  async loadDetail(exerciseId: number, force = false) {
    const slot = this.getSlot(this.details, exerciseId);
    return this.load(slot, DETAIL_TTL, force, async () => {
      const [exercises, stats, history, settings] = await Promise.all([
        this.loadExercises(force),
        api.stats(exerciseId),
        api.history(exerciseId, 35),
        this.loadSettings(force),
      ]);
      const exercise = exercises.find((item) => item.id === exerciseId);
      if (!exercise) throw new Error("Exercise not found.");
      return { exercise, stats, history, timezone: settings.timezone };
    });
  }

  async loadFullHistory(exerciseId: number, force = false) {
    const slot = this.getSlot(this.fullHistories, exerciseId);
    return this.load(slot, FULL_HISTORY_TTL, force, () =>
      fetchAll((limit, offset) => api.history(exerciseId, limit, offset)),
    );
  }

  async loadFullEntries(exerciseId: number, force = false) {
    const slot = this.getSlot(this.fullEntries, exerciseId);
    return this.load(slot, FULL_HISTORY_TTL, force, () =>
      fetchAll((limit, offset) => api.entries(exerciseId, limit, offset)),
    );
  }

  async loadResultsHistory(exerciseId: number, limit: number, force = false) {
    const slot = this.getSlot(this.resultsHistories, exerciseId);
    return this.load(slot, FULL_HISTORY_TTL, force, async () => {
      const days = await api.history(exerciseId, limit);
      return { days, hasMore: days.length === limit };
    });
  }

  saveResultsHistory(exerciseId: number, history: ResultsHistory) {
    this.resultsHistories.set(exerciseId, { value: history, updatedAt: Date.now() });
  }

  async loadEntriesForDay(exerciseId: number, date: string, force = false) {
    const slot = this.getSlot(this.entriesByDay, `${exerciseId}:${date}`);
    return this.load(slot, FULL_HISTORY_TTL, force, () =>
      fetchAll((limit, offset) => api.entriesForDay(exerciseId, date, limit, offset)),
    );
  }

  async loadSettings(force = false) {
    return this.load(this.settings, SETTINGS_TTL, force, () => api.settings());
  }

  saveSettings(settings: Settings) {
    this.settings = { value: settings, updatedAt: Date.now() };
    this.details.forEach((slot) => { slot.updatedAt = 0; });
  }

  invalidateExercise(exerciseId: number) {
    this.dashboard.updatedAt = 0;
    this.details.get(exerciseId) && (this.details.get(exerciseId)!.updatedAt = 0);
    this.fullHistories.get(exerciseId) && (this.fullHistories.get(exerciseId)!.updatedAt = 0);
    this.fullEntries.get(exerciseId) && (this.fullEntries.get(exerciseId)!.updatedAt = 0);
    this.resultsHistories.get(exerciseId) && (this.resultsHistories.get(exerciseId)!.updatedAt = 0);
    for (const [key, slot] of this.entriesByDay) {
      if (key.startsWith(`${exerciseId}:`)) slot.updatedAt = 0;
    }
  }

  invalidateExercises() {
    this.exercises.updatedAt = 0;
    this.dashboard.updatedAt = 0;
    this.details.forEach((slot) => { slot.updatedAt = 0; });
  }

  private getSlot<K, T>(slots: Map<K, CacheSlot<T>>, key: K) {
    let slot = slots.get(key);
    if (!slot) {
      slot = { updatedAt: 0 };
      slots.set(key, slot);
    }
    return slot;
  }

  private async loadExercises(force: boolean) {
    return this.load(this.exercises, DASHBOARD_TTL, force, () => api.exercises());
  }

  private async load<T>(slot: CacheSlot<T>, ttl: number, force: boolean, fetcher: () => Promise<T>) {
    if (!force && slot.value !== undefined && Date.now() - slot.updatedAt < ttl) return slot.value;
    if (slot.pending) return slot.pending;
    slot.pending = fetcher()
      .then((value) => {
        slot.value = value;
        slot.updatedAt = Date.now();
        return value;
      })
      .finally(() => { slot.pending = undefined; });
    return slot.pending;
  }
}

export const appDataCache = new AppDataCache();
