/**
 * Light / dark / system theme.
 *
 * Three states, not two. "System" is the default and it must stay reachable:
 * a reader whose machine switches to dark at sunset should not be stuck in the
 * light theme because they once tapped a toggle.
 *
 * The choice is written to <html data-theme="...">, which is what the
 * stylesheet keys off. Nothing else in the app knows about theming.
 */

import { useCallback, useEffect, useState } from "react";

export type ThemeChoice = "light" | "dark" | "system";

export const THEME_STORAGE_KEY = "democraseek.theme.v1";

function isThemeChoice(value: unknown): value is ThemeChoice {
  return value === "light" || value === "dark" || value === "system";
}

function readStoredTheme(): ThemeChoice {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    return isThemeChoice(stored) ? stored : "system";
  } catch {
    return "system";
  }
}

function apply(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === "system") {
    // No attribute: the stylesheet falls back to prefers-color-scheme.
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", choice);
  }
}

export function useTheme(): {
  theme: ThemeChoice;
  setTheme: (choice: ThemeChoice) => void;
  /** What is actually on screen right now, with "system" resolved. */
  resolved: "light" | "dark";
} {
  const [theme, setThemeState] = useState<ThemeChoice>(() => readStoredTheme());
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false,
  );

  useEffect(() => {
    apply(theme);
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      /* storage may be unavailable; the theme still applies for this session */
    }
  }, [theme]);

  useEffect(() => {
    const query = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!query) return;
    const onChange = (event: MediaQueryListEvent) => setSystemDark(event.matches);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  const setTheme = useCallback((choice: ThemeChoice) => setThemeState(choice), []);
  const resolved = theme === "system" ? (systemDark ? "dark" : "light") : theme;

  return { theme, setTheme, resolved };
}
