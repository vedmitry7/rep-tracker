/**
 * Unit tests for the web i18n runtime.
 *
 * Run with `npm test` (from frontend/). The `--import ./scripts/ts-hooks.mjs`
 * flag lets Node load the TypeScript dictionaries with extensionless imports.
 */
import assert from "node:assert/strict";
import test from "node:test";
import { SUPPORTED_LOCALES, getLocale, isSupportedLocale, setLocale, t } from "../src/i18n/index.ts";
import { formatNumber } from "../src/i18n/format.ts";

test("SUPPORTED_LOCALES lists every API language", () => {
  assert.deepEqual([...SUPPORTED_LOCALES], ["en", "ru", "es", "pt", "tr", "uk", "id", "hi", "kk", "pl", "fr"]);
});

test("isSupportedLocale guards known language codes", () => {
  assert.equal(isSupportedLocale("ru"), true);
  assert.equal(isSupportedLocale("de"), false);
  assert.equal(isSupportedLocale(undefined), false);
  assert.equal(isSupportedLocale(null), false);
});

test("setLocale switches the active dictionary", () => {
  setLocale("ru");
  assert.equal(getLocale(), "ru");
  assert.equal(t("common.today"), "Сегодня");
  assert.equal(t("home.openExercise", { name: "Присед" }), "Открыть Присед");
});

test("unknown or missing locales fall back to English", () => {
  setLocale("de");
  assert.equal(getLocale(), "en");
  assert.equal(t("common.today"), "Today");
  setLocale(undefined);
  assert.equal(getLocale(), "en");
});

test("plural entries pick the CLDR form for the locale", () => {
  setLocale("ru");
  assert.equal(t("results.daysCount", { count: 1 }), "1 день");
  assert.equal(t("results.daysCount", { count: 2 }), "2 дня");
  assert.equal(t("results.daysCount", { count: 5 }), "5 дней");
  assert.equal(t("results.daysCount", { count: 11 }), "11 дней");
  assert.equal(t("results.daysCount", { count: 21 }), "21 день");

  setLocale("id");
  assert.equal(t("results.daysCount", { count: 1 }), "1 hari");
  assert.equal(t("results.daysCount", { count: 3 }), "3 hari");

  setLocale("fr");
  assert.equal(t("results.daysCount", { count: 1 }), "1 jour");
  assert.equal(t("results.daysCount", { count: 2 }), "2 jours");
});

test("plural entries require a numeric count", () => {
  setLocale("en");
  assert.throws(() => t("results.daysCount", {}), /requires a numeric "count"/);
});

test("format helpers default to the active locale", () => {
  setLocale("ru");
  assert.equal(formatNumber(1000), (1000).toLocaleString("ru"));
  setLocale("en");
  assert.equal(formatNumber(1000), "1,000");
});

test.after(() => setLocale("en"));
