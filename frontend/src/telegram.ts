type Insets = {
  top: number;
  right: number;
  bottom: number;
  left: number;
};

type TelegramWebApp = {
  initData: string;
  isFullscreen?: boolean;
  contentSafeAreaInset?: Insets;
  ready: () => void;
  requestFullscreen?: () => void;
  setBackgroundColor?: (color: string) => void;
  setBottomBarColor?: (color: string) => void;
  setHeaderColor?: (color: string) => void;
  onEvent?: (eventType: "safeAreaChanged" | "contentSafeAreaChanged" | "fullscreenChanged", handler: () => void) => void;
};

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

const backgroundColor = "#080808";

function applyContentSafeArea(webApp: TelegramWebApp) {
  const inset = webApp.contentSafeAreaInset;
  const root = document.documentElement.style;
  root.setProperty("--telegram-content-safe-area-top", `${inset?.top ?? 0}px`);
  root.setProperty("--telegram-content-safe-area-right", `${inset?.right ?? 0}px`);
  root.setProperty("--telegram-content-safe-area-bottom", `${inset?.bottom ?? 0}px`);
  root.setProperty("--telegram-content-safe-area-left", `${inset?.left ?? 0}px`);
}

/** Configure the page only when it is hosted in a Telegram Mini App. */
export function initialiseTelegramMiniApp() {
  const webApp = window.Telegram?.WebApp;
  if (!webApp) return;

  webApp.ready();
  webApp.setHeaderColor?.(backgroundColor);
  webApp.setBackgroundColor?.(backgroundColor);
  webApp.setBottomBarColor?.(backgroundColor);
  applyContentSafeArea(webApp);

  const refreshSafeArea = () => applyContentSafeArea(webApp);
  webApp.onEvent?.("safeAreaChanged", refreshSafeArea);
  webApp.onEvent?.("contentSafeAreaChanged", refreshSafeArea);
  webApp.onEvent?.("fullscreenChanged", refreshSafeArea);

  if (!webApp.isFullscreen) webApp.requestFullscreen?.();
}

/**
 * Telegram signs this opaque query string. It is sent unchanged to the API,
 * where the bot token verifies it; the browser never receives that token.
 */
export function getTelegramInitData(): string {
  const initData = window.Telegram?.WebApp?.initData;
  if (!initData) throw new Error("Open Repka from the Telegram app.");
  return initData;
}
