/** A calm entry point before profile setup or an existing conversation. */

import { branding } from "../branding";
import type { ThemeChoice } from "../hooks/useTheme";
import type { UiLocale } from "../i18n";
import { useUi } from "../i18n";
import { BrandMark } from "./Header";
import { LanguageSelector } from "./LanguageSelector";
import { ThemeToggle } from "./ThemeToggle";

interface Props {
  theme: ThemeChoice;
  onThemeChange: (choice: ThemeChoice) => void;
  locale: UiLocale;
  onLocaleChange: (locale: string) => void;
  onStart: () => void;
}

export function Welcome({
  theme,
  onThemeChange,
  locale,
  onLocaleChange,
  onStart,
}: Props): JSX.Element {
  const { ui } = useUi();
  return (
    <div className="welcome">
      <header className="welcome__header">
        <div className="welcome__brand">
          {branding.logoUrl ? (
            <img src={branding.logoUrl} alt="" height={40} />
          ) : (
            <BrandMark />
          )}
          <span>{branding.appName}</span>
        </div>
        <div className="display-controls">
          <LanguageSelector locale={locale} onChange={onLocaleChange} />
          <ThemeToggle theme={theme} onChange={onThemeChange} />
        </div>
      </header>

      <main className="welcome__main" id="main">
        <section className="welcome__hero" aria-labelledby="welcome-title">
          <p className="welcome__eyebrow">{ui.welcome.eyebrow}</p>
          <h1 id="welcome-title">{ui.welcome.title}</h1>
          <p className="welcome__lead">{ui.welcome.lead}</p>
          <button type="button" className="button button--primary welcome__start" onClick={onStart}>
            {ui.welcome.start}
            <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
              <path d="M4 10h11M11 6l4 4-4 4" />
            </svg>
          </button>
        </section>

        <aside className="welcome__about" aria-label={ui.welcome.aboutLabel}>
          <span className="welcome__about-icon" aria-hidden="true">i</span>
          <div>
            <h2>{ui.welcome.aboutTitle}</h2>
            <p>{ui.welcome.aboutText}</p>
          </div>
        </aside>
      </main>
    </div>
  );
}
