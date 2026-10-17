import { useSyncExternalStore } from "react";
import { getLocale, subscribeToLocale, type AppLocale } from "./index";

/** React binding for the active locale: re-renders when it changes. */
export function useLocale(): AppLocale {
  return useSyncExternalStore(subscribeToLocale, getLocale, getLocale);
}
