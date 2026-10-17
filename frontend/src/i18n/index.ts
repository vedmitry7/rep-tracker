import { en } from "./en";
import { ru } from "./ru";
import { es } from "./es";
import { pt } from "./pt";
import { tr } from "./tr";
import { uk } from "./uk";
import { id } from "./id";
import { hi } from "./hi";
import { kk } from "./kk";
import { pl } from "./pl";
import { fr } from "./fr";

/** API-supported UI languages. */
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

/** A leaf value is either a plain template or a CLDR plural set. */
type Leaf = string | PluralForms;

/**
 * Every non-English dictionary must mirror the English key structure while
 * being allowed to define fewer or more CLDR plural categories (for example
 * Indonesian needs only `other`, Russian needs `one`/`few`/`many`/`other`).
 */
type DictValue<T> = T extends string
  ? string
  : T extends { other: string }
    ? PluralForms
    : { readonly [K in keyof T]: DictValue<T[K]> };

export type Dictionary = {
  readonly [K in keyof typeof en]: DictValue<(typeof en)[K]>;
};

const dictionaries: Record<AppLocale, Dictionary> = {
  en,
  ru,
  es,
  pt,
  tr,
  uk,
  id,
  hi,
  kk,
  pl,
  fr,
};

const DEFAULT_LOCALE: AppLocale = "en";
let activeLocale: AppLocale = DEFAULT_LOCALE;
const localeListeners = new Set<() => void>();

export function isSupportedLocale(value: unknown): value is AppLocale {
  return typeof value === "string" && (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

/** The dictionary currently used by `t()` and the format helpers. */
export function getLocale(): AppLocale {
  return activeLocale;
}

/**
 * Switch the active dictionary. Unknown or missing values fall back to
 * English so a bad `settings.language` can never break the UI.
 */
export function setLocale(value: string | null | undefined): AppLocale {
  const next = isSupportedLocale(value) ? value : DEFAULT_LOCALE;
  if (next === activeLocale) return next;
  activeLocale = next;
  for (const listener of localeListeners) listener();
  return next;
}

/** Subscribe to locale changes; used by `useLocale` to re-render the app. */
export function subscribeToLocale(listener: () => void): () => void {
  localeListeners.add(listener);
  return () => {
    localeListeners.delete(listener);
  };
}

function isPluralForms(value: unknown): value is PluralForms {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as PluralForms).other === "string"
  );
}

function lookupIn(dictionary: Dictionary, key: string): Leaf | undefined {
  let current: unknown = dictionary;
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
 * Translate a key using the active dictionary, falling back to English for an
 * unknown locale, a missing key, or a missing plural category. Plural entries
 * require a numeric `count` param and pick the CLDR form for the locale.
 */
export function t(key: TranslationKey, params: TranslationParams = {}): string {
  const entry = lookupIn(dictionaries[activeLocale], key) ?? lookupIn(en, key);
  if (entry === undefined) return key;
  if (typeof entry === "string") return interpolate(entry, params);
  const count = params.count;
  if (typeof count !== "number") {
    throw new Error(`i18n: plural key "${key}" requires a numeric "count" param`);
  }
  const category = new Intl.PluralRules(activeLocale).select(count);
  const englishEntry = lookupIn(en, key);
  const template =
    entry[category] ??
    (isPluralForms(englishEntry) ? englishEntry[category] : undefined) ??
    entry.other;
  return interpolate(template, { ...params, count });
}
