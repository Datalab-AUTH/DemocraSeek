/**
 * Application header.
 *
 * The profile used to occupy a permanent column even though it is changed once
 * per session. It now lives behind a chip here: visible at a glance, one click
 * to open, and the conversation gets the full width it needs.
 */

import { useEffect, useRef, useState } from "react";

import type { OnboardingConfig, Profile } from "../api/types";
import { branding } from "../branding";
import type { ThemeChoice } from "../hooks/useTheme";
import type { UiLocale } from "../i18n";
import { useUi } from "../i18n";
import { LanguageSelector } from "./LanguageSelector";
import { ThemeToggle } from "./ThemeToggle";

interface Props {
  config: OnboardingConfig | null;
  profile: Profile | null;
  theme: ThemeChoice;
  onThemeChange: (choice: ThemeChoice) => void;
  locale: UiLocale;
  onLocaleChange: (locale: string) => void;
  onChangeProfile: () => void;
  onResetProfile: () => void;
  onNewConversation: () => void;
  canStartNewConversation: boolean;
}

function labelFor(
  config: OnboardingConfig,
  locale: UiLocale,
  dimension: string,
  code: string,
): string {
  const question = config.questions.find((item) => item.dimension === dimension);
  const base = question?.choices.find((choice) => choice.code === code)?.label ?? code;
  if (locale === config.default_locale || !question) return base;
  const translated = config.translations.find((item) => item.locale === locale);
  return translated?.questions[question.id]?.choices[code]?.label ?? base;
}

/**
 * A speech bubble with a check inside: the product is answers you can verify.
 * Inline SVG rather than an icon package - it is eleven elements and it inherits
 * the brand gradient, so there is nothing to install and nothing to keep in sync.
 */
export function BrandMark(): JSX.Element {
  return (
    <svg className="app__mark" viewBox="0 0 40 40" role="img" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="ds-mark" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--brand)" />
          <stop offset="100%" stopColor="var(--accent)" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="11" fill="url(#ds-mark)" />
      <path
        d="M11 13.5h18v11.5a2 2 0 0 1-2 2h-8.6L14 31v-4h-1a2 2 0 0 1-2-2V13.5Z"
        fill="rgb(255 255 255 / 92%)"
      />
      <path
        d="m16.4 20.4 2.7 2.7 5-5.4"
        fill="none"
        stroke="var(--brand-strong)"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Header({
  config,
  profile,
  theme,
  onThemeChange,
  locale,
  onLocaleChange,
  onChangeProfile,
  onResetProfile,
  onNewConversation,
  canStartNewConversation,
}: Props): JSX.Element {
  const { ui } = useUi();
  const [open, setOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent): void {
      const target = event.target as Node;
      if (!popoverRef.current?.contains(target) && !triggerRef.current?.contains(target)) {
        setOpen(false);
      }
    }
    // Escape is handled at document level, not on the popover: focus stays on
    // the trigger after opening, so a handler bound to the popover never sees it.
    function onKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const entries =
    config && profile
      ? ([
          [ui.header.role, labelFor(config, locale, "role", profile.role_code)],
          [ui.header.intent, labelFor(config, locale, "intent", profile.intent_code)],
          [ui.header.support, labelFor(config, locale, "support", profile.support_code)],
          [ui.header.mode, labelFor(config, locale, "mode", profile.mode_code)],
        ] as const)
      : [];

  return (
    <header className="app__header">
      <div className="app__header-inner">
        <div className="app__brand">
          {branding.logoUrl ? (
            <img src={branding.logoUrl} alt="" height={34} />
          ) : (
            <BrandMark />
          )}
          <div className="app__names">
            <h1>{branding.appName}</h1>
          </div>
        </div>

        <div className="app__actions">
          <div className="display-controls">
            <LanguageSelector
              locale={locale}
              locales={config?.locales}
              onChange={onLocaleChange}
            />
            <ThemeToggle theme={theme} onChange={onThemeChange} />
          </div>

          {profile && config ? (
            <>
              <button
                type="button"
                className="button button--ghost header__new-conversation"
                onClick={onNewConversation}
                disabled={!canStartNewConversation}
              >
                <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
                  <path d="M10 4v12M4 10h12" />
                </svg>
                <span>{ui.header.newConversation}</span>
              </button>

              <div className="profile-chip__wrap">
                <button
                  ref={triggerRef}
                  type="button"
                  className="profile-chip"
                  aria-expanded={open}
                  aria-haspopup="dialog"
                  aria-label={ui.header.preferences}
                  onClick={() => setOpen((value) => !value)}
                >
                  <span className="profile-chip__text">
                    <span className="profile-chip__value">
                      {labelFor(config, locale, "role", profile.role_code)}
                    </span>
                    <span className="profile-chip__label">
                      {labelFor(config, locale, "mode", profile.mode_code)}
                    </span>
                  </span>
                  <svg
                    className={open ? "profile-chip__chevron is-open" : "profile-chip__chevron"}
                    viewBox="0 0 12 12"
                    aria-hidden="true"
                    focusable="false"
                  >
                    <path
                      d="m2.5 4.5 3.5 3.5 3.5-3.5"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>

                {open ? (
                  <div
                    ref={popoverRef}
                    className="profile-popover"
                    role="dialog"
                    aria-label={ui.header.tailoredDialog}
                  >
                    <h2 className="profile__heading">{ui.header.tailoredTitle}</h2>
                    <dl className="profile__list">
                      {entries.map(([term, label]) => (
                        <div key={term} className="profile__entry">
                          <dt>{term}</dt>
                          <dd>{label}</dd>
                        </div>
                      ))}
                    </dl>
                    <p className="profile__note">{ui.header.note}</p>
                    <div className="profile__actions">
                      <button
                        type="button"
                        className="button button--ghost"
                        onClick={() => {
                          setOpen(false);
                          onChangeProfile();
                        }}
                      >
                        {ui.header.update}
                      </button>
                      <button
                        type="button"
                        className="button button--ghost"
                        onClick={() => {
                          setOpen(false);
                          onResetProfile();
                        }}
                      >
                        {ui.header.startOver}
                      </button>
                    </div>
                    <p className="profile__privacy">{ui.header.privacy}</p>
                  </div>
                ) : null}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
