/** A non-identifying presentation preference stored only in this browser. */

import { useCallback, useState } from "react";

export const ONBOARDING_LOCALE_STORAGE_KEY = "democraseek.onboarding-locale.v1";

function readStoredLocale(): string | null {
  try {
    const value = window.localStorage.getItem(ONBOARDING_LOCALE_STORAGE_KEY);
    return value?.trim() || null;
  } catch {
    return null;
  }
}

export function useOnboardingLocale(): {
  locale: string | null;
  saveLocale: (locale: string) => void;
} {
  const [locale, setLocale] = useState<string | null>(() => readStoredLocale());

  const saveLocale = useCallback((next: string) => {
    setLocale(next);
    try {
      window.localStorage.setItem(ONBOARDING_LOCALE_STORAGE_KEY, next);
    } catch {
      /* Private browsing may disable storage; the current session still works. */
    }
  }, []);

  return { locale, saveLocale };
}
