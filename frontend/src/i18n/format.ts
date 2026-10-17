import { t } from "./index";
import type { ExerciseEntry } from "../types";

/**
 * User-visible date/number formatting with an explicit locale override.
 * The locale defaults to `undefined` (browser locale), preserving the
 * current visible behaviour; stage 2 will pass the saved app locale.
 */

export function formatNumber(value: number, locale?: string): string {
  return value.toLocaleString(locale);
}

export function formatDate(value: string, locale?: string): string {
  return new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(`${value}T12:00:00`));
}

export function formatTime(value: string, timeZone?: string, locale?: string): string {
  return new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  }).format(new Date(value));
}

export function formatMonth(value: Date, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { month: "short", year: "2-digit" }).format(value);
}

export function formatMonthShort(value: Date, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { month: "short" }).format(value);
}

export function formatWeekdayNarrow(value: Date, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { weekday: "narrow" }).format(value);
}

export function formatWeekdayShort(value: Date, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { weekday: "short" }).format(value);
}

export function formatDayNumeric(value: Date, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { day: "numeric" }).format(value);
}

export function totalReps(entry: ExerciseEntry): number {
  return entry.reps.reduce((sum, reps) => sum + reps, 0);
}

export function formatSets(reps: number[]): string {
  return reps.length > 1 && reps.every((value) => value === reps[0])
    ? `${reps.length} × ${reps[0]}`
    : reps.join(" + ");
}

export function formatResultMoment(
  entry: ExerciseEntry,
  today: string,
  timezone: string,
  locale?: string,
): string {
  const performedOn =
    entry.performed_on === today ? t("common.today") : formatDate(entry.performed_on, locale);
  return t("time.moment", { date: performedOn, time: formatTime(entry.created_at, timezone, locale) });
}

export function relativeEntryTime(value: string): string {
  const elapsed = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.floor(elapsed / 60_000);
  if (minutes < 1) return t("time.justNow");
  if (minutes < 60) return t("time.minutesAgo", { count: minutes });
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return t("time.hoursAgo", { count: hours });
  const days = Math.floor(hours / 24);
  if (days === 1) return t("time.yesterday");
  if (days < 7) return t("time.daysAgo", { count: days });
  return formatDate(value.slice(0, 10));
}

export function formatPercentChange(percent: number | null): string {
  if (percent === null) return "—";
  return `${percent >= 0 ? "+" : ""}${percent}%`;
}

export function formatWeekRange(start: string, end: string, locale?: string): string {
  const startDate = new Date(`${start}T12:00:00`);
  const endDate = new Date(`${end}T12:00:00`);
  const month = new Intl.DateTimeFormat(locale, { month: "short" });
  return startDate.getMonth() === endDate.getMonth()
    ? `${startDate.getDate()}–${endDate.getDate()} ${month.format(endDate)}`
    : `${startDate.getDate()} ${month.format(startDate)} – ${endDate.getDate()} ${month.format(endDate)}`;
}

// Keep the frontend grammar aligned with bot.app.services.result_parser:
// `4x10` / `4×10`, numbers separated by spaces, commas, or plus signs.
export function parseQuickResult(value: string): number[] {
  const text = value.trim();
  if (!text) throw new Error(t("entry.emptySetsError"));
  let parsed: number[];
  const repeated = text.match(/^(\d+)\s*[xX×*]\s*(\d+)$/);
  if (repeated) {
    const count = Number(repeated[1]);
    const reps = Number(repeated[2]);
    parsed = Array.from({ length: count }, () => reps);
  } else if (/^\d+(?:\s+\d+)*$/.test(text)) {
    parsed = text.split(/\s+/).map(Number);
  } else if (/^\d+(?:\s*[,+]\s*\d+)*$/.test(text)) {
    parsed = text.split(/\s*[,+]\s*/).map(Number);
  } else {
    throw new Error(t("entry.formatError"));
  }
  if (
    !parsed.length ||
    parsed.length > 100 ||
    parsed.some((item) => !Number.isInteger(item) || item < 1 || item > 10000)
  ) {
    throw new Error(t("entry.rangeError"));
  }
  return parsed;
}
