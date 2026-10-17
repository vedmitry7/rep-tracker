/**
 * Node loader hook for the i18n tests.
 *
 * Node strips TypeScript types on its own, but ESM still needs explicit file
 * extensions. The frontend imports its modules without extensions, so this hook
 * resolves relative specifiers to `.ts`/`.tsx` (or `/index.ts`) to mirror what
 * Vite does during a build.
 */
import { registerHooks } from "node:module";
import { existsSync } from "node:fs";

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith(".") && !/\.[cm]?[jt]sx?$/.test(specifier)) {
      for (const candidate of [`${specifier}.ts`, `${specifier}.tsx`, `${specifier}/index.ts`]) {
        try {
          if (existsSync(new URL(candidate, context.parentURL))) {
            return nextResolve(candidate, context);
          }
        } catch {
          // Not a valid relative URL; fall through to the default resolver.
        }
      }
    }
    return nextResolve(specifier, context);
  },
});
