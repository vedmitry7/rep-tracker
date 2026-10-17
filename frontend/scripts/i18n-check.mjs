/**
 * i18n key check for the Repka web app (stage 1: English-only dictionary).
 *
 * Usage: `npm run i18n:check` (from frontend/).
 *
 * Verifies that:
 * 1. Every `t("some.key")` call in src/ (outside src/i18n/en.ts) references a
 *    key that exists in the English dictionary (no missing/unknown keys).
 * 2. Every dictionary leaf is actually used in code (no dead keys).
 * 3. Every `{placeholder}` in a template is provided at each call site
 *    (plural entries additionally require a `count` param).
 * 4. Plural forms of one entry use a consistent placeholder set, so future
 *    translations cannot silently drop a parameter.
 *
 * Exit code is non-zero when any of these checks fail.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(fileURLToPath(import.meta.url), "..", "..", "src");
const dictionaryPath = join(root, "i18n", "en.ts");
const PLURAL_CATEGORIES = new Set(["zero", "one", "two", "few", "many", "other"]);

function placeholdersOf(template) {
  return new Set([...template.matchAll(/\{(\w+)\}/g)].map((m) => m[1]));
}

/** Minimal parser for the `export const en = {...} as const` dictionary. */
function parseDictionary(source) {
  const leaves = new Map(); // key -> { kind, placeholders, forms? }
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
          const union = new Set();
          for (const child of obj.children) {
            const leaf = leaves.get(`${base}.${child}`);
            forms.add(child);
            leaf?.placeholders.forEach((p) => union.add(p));
            leaves.delete(`${base}.${child}`);
          }
          leaves.set(base, { kind: "plural", placeholders: union, forms });
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
const leaves = parseDictionary(readFileSync(dictionaryPath, "utf8"));
if (leaves.size === 0) errors.push("dictionary: no keys parsed from src/i18n/en.ts");

const usedKeys = new Map(); // key -> count
let callSites = 0;
for (const file of listSources(root)) {
  if (file === dictionaryPath) continue;
  const source = readFileSync(file, "utf8");
  const name = relative(root, file);
  for (const usage of findUsages(source)) {
    callSites++;
    usedKeys.set(usage.key, (usedKeys.get(usage.key) ?? 0) + 1);
    const leaf = leaves.get(usage.key);
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

for (const key of leaves.keys()) {
  if (!usedKeys.has(key)) errors.push(`dictionary: key "${key}" is never used in src/`);
}

for (const [key, leaf] of leaves) {
  if (leaf.kind === "plural" && !leaf.forms.has("other")) {
    errors.push(`dictionary: plural key "${key}" must define an "other" form`);
  }
}

console.log(`i18n: ${leaves.size} keys, ${callSites} call sites`);
for (const w of warnings) console.log(`warning: ${w}`);
if (errors.length > 0) {
  for (const e of errors) console.log(`error: ${e}`);
  console.log(`i18n:check FAILED (${errors.length} problem${errors.length === 1 ? "" : "s"})`);
  process.exit(1);
}
console.log("i18n:check OK");
