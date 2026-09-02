/** Persist and apply the light, dark or system theme. */

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
    // No attribute lets CSS follow the system preference.
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", choice);
  }
}

export function useTheme(): {
  theme: ThemeChoice;
  setTheme: (choice: ThemeChoice) => void;
  /** Effective light or dark theme. */
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
