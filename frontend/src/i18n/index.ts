import { en } from "./en";

/** API-supported UI languages. Stage 1 ships only the English dictionary. */
export const SUPPORTED_LOCALES = [
  "en",
  "ru",
  "es",
  "pt",
  "tr",
  "uk",
  "id",
  "hi",
  "kk",
  "pl",
  "fr",
] as const;
export type AppLocale = (typeof SUPPORTED_LOCALES)[number];

export type PluralForms = {
  zero?: string;
  one?: string;
  two?: string;
  few?: string;
  many?: string;
  other: string;
};

type Dictionary = typeof en;

/**
 * Stage 1: the web UI is intentionally English-only. The saved settings
 * language is still persisted via the API, and stage 2 will return the
 * matching dictionary here based on it.
 */
export function getLocale(): AppLocale {
  return "en";
}

function isPluralForms(value: unknown): value is PluralForms {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as PluralForms).other === "string"
  );
}

function lookup(key: string): string | PluralForms | undefined {
  let current: unknown = en;
  for (const part of key.split(".")) {
    if (typeof current !== "object" || current === null) return undefined;
    current = (current as Record<string, unknown>)[part];
  }
  if (typeof current === "string" || isPluralForms(current)) return current;
  return undefined;
}

type PathImpl<T, Prefix extends string> = {
  [K in keyof T]: T[K] extends string
    ? `${Prefix}${K & string}`
    : T[K] extends PluralForms
      ? `${Prefix}${K & string}`
      : T[K] extends Record<string, unknown>
        ? PathImpl<T[K], `${Prefix}${K & string}.`>
        : never;
}[keyof T];

/** Dot-path to a dictionary leaf, e.g. "home.emptyTitle". */
export type TranslationKey = PathImpl<Dictionary, "">;

export type TranslationParams = Record<string, string | number>;

function interpolate(template: string, params: TranslationParams): string {
  return template.replace(/\{(\w+)\}/g, (match, name: string) => {
    const value = params[name];
    return value === undefined ? match : String(value);
  });
}

/**
 * Translate a key, filling `{placeholders}` from params. Plural entries
 * require a numeric `count` param and pick the CLDR form for the locale.
 */
export function t(key: TranslationKey, params: TranslationParams = {}): string {
  const entry = lookup(key);
  if (entry === undefined) return key;
  if (typeof entry === "string") return interpolate(entry, params);
  const count = params.count;
  if (typeof count !== "number") {
    throw new Error(`i18n: plural key "${key}" requires a numeric "count" param`);
  }
  const category = new Intl.PluralRules(getLocale()).select(count);
  return interpolate(entry[category] ?? entry.other, { ...params, count });
}
