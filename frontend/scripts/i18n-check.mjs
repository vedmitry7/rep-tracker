/**
 * i18n key check for the Repka web app.
 *
 * Usage: `npm run i18n:check` (from frontend/).
 *
 * Verifies that:
 * 1. Every non-English dictionary (src/i18n/<locale>.ts) mirrors the English
 *    reference exactly: same keys, same text/plural kind, same `{placeholder}`
 *    set, and no extra keys.
 * 2. Every plural entry defines exactly the CLDR categories used by that
 *    locale's `Intl.PluralRules` (so translations cannot silently drop a form).
 * 3. Every `t("some.key")` call in src/ references a key that exists in the
 *    English dictionary, provides all required `{placeholder}` params, and
 *    passes a numeric `count` for plural keys.
 * 4. Every dictionary leaf is actually used in code (no dead keys).
 *
 * Exit code is non-zero when any of these checks fail.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const i18nDir = join(fileURLToPath(import.meta.url), "..", "..", "src", "i18n");
const root = join(i18nDir, "..");
const PLURAL_CATEGORIES = new Set(["zero", "one", "two", "few", "many", "other"]);

/** Read `SUPPORTED_LOCALES` from index.ts so the locale list has one source. */
function readLocales() {
  const source = readFileSync(join(i18nDir, "index.ts"), "utf8");
  const match = source.match(/SUPPORTED_LOCALES\s*=\s*\[([\s\S]*?)\]\s*as\s+const/);
  if (!match) return [];
  return [...match[1].matchAll(/"([a-z]{2}(?:-[A-Za-z]{2,4})?)"/g)].map((m) => m[1]);
}

function placeholdersOf(template) {
  return new Set([...template.matchAll(/\{(\w+)\}/g)].map((m) => m[1]));
}

/** Minimal parser for `export const xx = {...} as const` dictionaries. */
function parseDictionary(source) {
  const leaves = new Map(); // key -> { kind, placeholders, forms?, formPlaceholders? }
  const stack = []; // { name, children: string[] }
  const pathOf = (name) => [...stack.map((s) => s.name), name].filter(Boolean).join(".");

  for (const rawLine of source.split("\n")) {
    const line = rawLine.trim();
    let m;
    if (/^(export\s+const\s+\w+\s*=\s*)?\{\s*$/.test(line)) {
      stack.push({ name: "", children: [] });
    } else if ((m = line.match(/^(\w+)\s*:\s*\{\s*$/))) {
      stack.push({ name: m[1], children: [] });
    } else if ((m = line.match(/^(\w+)\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$/))) {
      const key = pathOf(m[1]);
      leaves.set(key, { kind: "text", placeholders: placeholdersOf(m[2]) });
      stack[stack.length - 1]?.children.push(m[1]);
    } else if (/^\}\s*(as\s+const\s*;)?\s*,?\s*$/.test(line)) {
      const obj = stack.pop();
      if (obj && obj.name && obj.children.length > 0) {
        const base = [...stack.map((s) => s.name), obj.name].filter(Boolean).join(".");
        if (obj.children.every((c) => PLURAL_CATEGORIES.has(c))) {
          const forms = new Set();
          const formPlaceholders = new Map();
          const union = new Set();
          for (const child of obj.children) {
            const leaf = leaves.get(`${base}.${child}`);
            forms.add(child);
            formPlaceholders.set(child, leaf?.placeholders ?? new Set());
            leaf?.placeholders.forEach((p) => union.add(p));
            leaves.delete(`${base}.${child}`);
          }
          leaves.set(base, { kind: "plural", placeholders: union, forms, formPlaceholders });
        }
      }
    }
  }
  return leaves;
}

function listSources(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...listSources(full));
    else if (/\.(ts|tsx)$/.test(entry)) out.push(full);
  }
  return out;
}

/** Split a `{...}` literal into top-level comma segments. */
function splitTopLevel(text) {
  const parts = [];
  let depth = 0;
  let current = "";
  for (const ch of text) {
    if (ch === "{" || ch === "(" || ch === "[") depth++;
    if (ch === "}" || ch === ")" || ch === "]") depth--;
    if (ch === "," && depth === 0) {
      parts.push(current);
      current = "";
    } else current += ch;
  }
  if (current.trim()) parts.push(current);
  return parts;
}

function paramNames(objectLiteral) {
  const names = new Set();
  const inner = objectLiteral.replace(/^\s*\{/, "").replace(/\}\s*$/, "");
  for (const part of splitTopLevel(inner)) {
    const m = part.match(/^\s*([A-Za-z_$][\w$]*)/);
    if (m) names.add(m[1]);
  }
  return names;
}

/** Find `t("key")` / `t("key", {...})` call sites in a source file. */
function findUsages(source) {
  const usages = [];
  const re = /(?<![A-Za-z0-9_$])t\(\s*"([^"\\]+)"(?:\s*,\s*(\{[\s\S]*?\}))?\s*\)/g;
  let m;
  while ((m = re.exec(source)) !== null) {
    usages.push({ key: m[1], params: m[2] ? paramNames(m[2]) : new Set(), index: m.index });
  }
  return usages;
}

const errors = [];
const warnings = [];

const locales = readLocales();
if (locales.length === 0) errors.push("dictionary: could not read SUPPORTED_LOCALES from src/i18n/index.ts");

const reference = parseDictionary(readFileSync(join(i18nDir, "en.ts"), "utf8"));
if (reference.size === 0) errors.push("dictionary: no keys parsed from src/i18n/en.ts");

const dictionaryPaths = new Set(locales.map((locale) => join(i18nDir, `${locale}.ts`)));

for (const locale of locales) {
  if (locale === "en") continue;
  const file = join(i18nDir, `${locale}.ts`);
  let leaves;
  try {
    leaves = parseDictionary(readFileSync(file, "utf8"));
  } catch {
    errors.push(`i18n/${locale}.ts: file is missing`);
    continue;
  }
  if (leaves.size === 0) {
    errors.push(`i18n/${locale}.ts: no keys parsed`);
    continue;
  }
  for (const [key, ref] of reference) {
    if (!leaves.has(key)) {
      errors.push(`${locale}: missing key "${key}"`);
      continue;
    }
    const leaf = leaves.get(key);
    if (leaf.kind !== ref.kind) {
      errors.push(`${locale}: key "${key}" is ${leaf.kind} but English is ${ref.kind}`);
      continue;
    }
    const missingParams = [...ref.placeholders].filter((p) => !leaf.placeholders.has(p));
    const extraParams = [...leaf.placeholders].filter((p) => !ref.placeholders.has(p));
    if (missingParams.length || extraParams.length) {
      errors.push(
        `${locale}: key "${key}" placeholders differ from English ` +
          `(missing: ${missingParams.join(", ") || "none"}; extra: ${extraParams.join(", ") || "none"})`,
      );
    }
    if (leaf.kind === "plural") {
      const required = new Set(new Intl.PluralRules(locale).resolvedOptions().pluralCategories);
      const absent = [...required].filter((form) => !leaf.forms.has(form));
      if (absent.length) errors.push(`${locale}: plural key "${key}" is missing required form(s): ${absent.join(", ")}`);
      const unused = [...leaf.forms].filter((form) => !required.has(form));
      if (unused.length) errors.push(`${locale}: plural key "${key}" defines form(s) ${locale} never uses: ${unused.join(", ")}`);
      for (const [form, placeholders] of leaf.formPlaceholders) {
        const formMissing = [...ref.placeholders].filter((p) => !placeholders.has(p));
        const formExtra = [...placeholders].filter((p) => !ref.placeholders.has(p));
        if (formMissing.length || formExtra.length) {
          errors.push(
            `${locale}: plural key "${key}" form "${form}" placeholders differ from English ` +
              `(missing: ${formMissing.join(", ") || "none"}; extra: ${formExtra.join(", ") || "none"})`,
          );
        }
      }
    }
  }
  for (const key of leaves.keys()) {
    if (!reference.has(key)) errors.push(`${locale}: unexpected key "${key}"`);
  }
}

const usedKeys = new Map(); // key -> count
let callSites = 0;
for (const file of listSources(root)) {
  if (dictionaryPaths.has(file)) continue;
  const source = readFileSync(file, "utf8");
  const name = relative(root, file);
  for (const usage of findUsages(source)) {
    callSites++;
    usedKeys.set(usage.key, (usedKeys.get(usage.key) ?? 0) + 1);
    const leaf = reference.get(usage.key);
    if (!leaf) {
      errors.push(`${name}: unknown i18n key "${usage.key}"`);
      continue;
    }
    const missing = [...leaf.placeholders].filter((p) => !usage.params.has(p));
    if (missing.length > 0) {
      errors.push(`${name}: t("${usage.key}") is missing params: ${missing.join(", ")}`);
    }
    if (leaf.kind === "plural" && !usage.params.has("count")) {
      errors.push(`${name}: plural key "${usage.key}" requires a numeric "count" param`);
    }
    const extra = [...usage.params].filter((p) => !leaf.placeholders.has(p));
    if (extra.length > 0) {
      warnings.push(`${name}: t("${usage.key}") passes unused params: ${extra.join(", ")}`);
    }
  }
}

for (const key of reference.keys()) {
  if (!usedKeys.has(key)) errors.push(`dictionary: key "${key}" is never used in src/`);
}

for (const [key, leaf] of reference) {
  if (leaf.kind === "plural" && !leaf.forms.has("other")) {
    errors.push(`dictionary: plural key "${key}" must define an "other" form`);
  }
}

console.log(`i18n: ${locales.length} locales, ${reference.size} keys, ${callSites} call sites`);
for (const w of warnings) console.log(`warning: ${w}`);
if (errors.length > 0) {
  for (const e of errors) console.log(`error: ${e}`);
  console.log(`i18n:check FAILED (${errors.length} problem${errors.length === 1 ? "" : "s"})`);
  process.exit(1);
}
console.log("i18n:check OK");
