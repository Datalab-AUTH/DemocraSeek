/** Persistent interface-language control shared by welcome, onboarding and chat. */

import { useEffect, useState } from "react";

import type { LocaleOption } from "../api/types";
import type { UiLocale } from "../i18n";
import { useUi } from "../i18n";

export const DEFAULT_LOCALES: LocaleOption[] = [
  { code: "en", display_name: "English", native_name: "English" },
  { code: "el", display_name: "Greek", native_name: "Ελληνικά" },
  { code: "fr", display_name: "French", native_name: "Français" },
  { code: "es", display_name: "Spanish", native_name: "Español" },
  {
    code: "nl-BE",
    display_name: "Dutch (Belgium)",
    native_name: "Nederlands (België)",
  },
];

const MOBILE_MAX_WIDTH = 720;

interface Props {
  locale: UiLocale;
  locales?: LocaleOption[];
  onChange: (locale: string) => void;
}

/** Uppercase language tag for compact mobile labels (e.g. nl-BE → NL). */
function shortLabel(code: string): string {
  return code.split("-")[0]!.toUpperCase();
}

function useCompactLanguageLabels(maxWidth = MOBILE_MAX_WIDTH): boolean {
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(`(max-width: ${maxWidth}px)`);
    function sync(): void {
      setCompact(media.matches);
    }
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, [maxWidth]);

  return compact;
}

export function LanguageSelector({
  locale,
  locales = DEFAULT_LOCALES,
  onChange,
}: Props): JSX.Element {
  const { ui } = useUi();
  const compact = useCompactLanguageLabels();

  return (
    <div className={compact ? "language-selector is-compact" : "language-selector"}>
      <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
        <circle cx="10" cy="10" r="7.2" />
        <path d="M2.8 10h14.4M10 2.8c2.2 2 3.2 4.4 3.2 7.2S12.2 15.2 10 17.2C7.8 15.2 6.8 12.8 6.8 10S7.8 4.8 10 2.8Z" />
      </svg>
      <label className="visually-hidden" htmlFor="interface-language">
        {ui.language.label}
      </label>
      <select
        id="interface-language"
        value={locale}
        aria-label={ui.language.label}
        title={ui.language.label}
        onChange={(event) => onChange(event.target.value)}
      >
        {locales.map((option) => (
          <option key={option.code} value={option.code}>
            {compact ? shortLabel(option.code) : option.native_name}
          </option>
        ))}
      </select>
    </div>
  );
}
