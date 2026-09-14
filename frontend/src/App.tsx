/** Application shell: loads configuration, owns the profile and the conversation. */

import { useCallback, useEffect, useState } from "react";

import { fetchCorpus, fetchOnboardingConfig } from "./api/client";
import type { Citation, CorpusDocument, OnboardingConfig } from "./api/types";
import { AnswerMessage } from "./components/AnswerMessage";
import { ChatPanel, type Turn } from "./components/ChatPanel";
import { EmptyState } from "./components/EmptyState";
import { Footer } from "./components/Footer";
import { Header } from "./components/Header";
import { Onboarding } from "./components/Onboarding";
import { SourceDrawer } from "./components/SourceDrawer";
import { Welcome } from "./components/Welcome";
import { useOnboardingLocale } from "./hooks/useOnboardingLocale";
import { useProfile } from "./hooks/useProfile";
import { useTheme } from "./hooks/useTheme";
import { getUiCopy, normalizeUiLocale, UiProvider } from "./i18n";

export const WELCOME_SESSION_KEY = "democraseek.welcome.entered.v1";

function hasEnteredThisSession(): boolean {
  try {
    return window.sessionStorage.getItem(WELCOME_SESSION_KEY) === "1";
  } catch {
    return false;
  }
}

export function App(): JSX.Element {
  const [config, setConfig] = useState<OnboardingConfig | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [documents, setDocuments] = useState<CorpusDocument[]>([]);
  const [pendingFiles, setPendingFiles] = useState<string[]>([]);
  const [examples, setExamples] = useState<string[]>([]);
  const { profile, saveProfile, resetProfile } = useProfile();
  const { locale: storedLocale, saveLocale } = useOnboardingLocale();
  const { theme, setTheme } = useTheme();
  const [hasEntered, setHasEntered] = useState(hasEnteredThisSession);
  const [editingProfile, setEditingProfile] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [openCitation, setOpenCitation] = useState<Citation | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchOnboardingConfig()
      .then((result) => {
        if (!cancelled) setConfig(result);
      })
      .catch((caught: Error) => {
        if (!cancelled) setConfigError(caught.message);
      });
    // Corpus hints are optional and must not block the app.
    fetchCorpus()
      .then((result) => {
        if (cancelled) return;
        setDocuments(result.documents);
        setPendingFiles(result.pending_files ?? []);
        setExamples(result.suggested_questions ?? []);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const newConversation = useCallback(() => {
    setTurns([]);
    setOpenCitation(null);
  }, []);

  // A policy-version change requires fresh onboarding.
  const activeProfile =
    config && profile?.policy_version === config.policy_version ? profile : null;

  const requestedLocale = normalizeUiLocale(storedLocale);
  const onboardingLocale =
    config && config.locales.some((option) => option.code === storedLocale)
      ? normalizeUiLocale(storedLocale)
      : normalizeUiLocale(config?.default_locale ?? requestedLocale);
  const ui = getUiCopy(onboardingLocale);
  const localized = (content: JSX.Element): JSX.Element => (
    <UiProvider locale={onboardingLocale}>{content}</UiProvider>
  );

  if (!hasEntered) {
    return localized(
      <Welcome
        theme={theme}
        onThemeChange={setTheme}
        locale={onboardingLocale}
        onLocaleChange={saveLocale}
        onStart={() => {
          try {
            window.sessionStorage.setItem(WELCOME_SESSION_KEY, "1");
          } catch {
            /* The in-memory state is sufficient when session storage is unavailable. */
          }
          setHasEntered(true);
        }}
      />,
    );
  }

  const header = (
    <Header
      config={config}
      profile={editingProfile ? null : activeProfile}
      theme={theme}
      onThemeChange={setTheme}
      locale={onboardingLocale}
      onLocaleChange={saveLocale}
      onChangeProfile={() => setEditingProfile(true)}
      onResetProfile={() => {
        resetProfile();
        newConversation();
      }}
      onNewConversation={newConversation}
      canStartNewConversation={turns.length > 0}
    />
  );

  if (configError) {
    return localized(
      <div className="app">
        {header}
        <main className="app__main">
          <div className="card card--message">
            <p className="form-error" role="alert">
              {ui.app.configError}
            </p>
          </div>
        </main>
        <Footer />
      </div>,
    );
  }

  if (!config) {
    return localized(
      <div className="app">
        {header}
        <main className="app__main">
          <div className="card card--message">
            <p aria-live="polite">{ui.app.loading}</p>
          </div>
        </main>
        <Footer />
      </div>,
    );
  }

  const needsOnboarding = !activeProfile || editingProfile;

  return localized(
    <div className="app">
      {header}
      <main
        className={
          needsOnboarding
            ? "app__main app__main--onboarding"
            : "app__main app__main--chat"
        }
        id="main"
      >
        {needsOnboarding ? (
          <Onboarding
            config={config}
            locale={onboardingLocale}
            initialProfile={activeProfile}
            onComplete={(next) => {
              saveProfile(next);
              setEditingProfile(false);
            }}
            onCancel={activeProfile ? () => setEditingProfile(false) : undefined}
          />
        ) : (
          <ChatPanel
            profile={activeProfile!}
            turns={turns}
            onTurnsChange={setTurns}
            onOpenSource={setOpenCitation}
            renderEmpty={(onPick) => (
              <EmptyState
                documents={documents}
                exampleQuestions={examples}
                pendingFiles={pendingFiles}
                onPickExample={onPick}
              />
            )}
            renderAnswer={(response) => (
              <AnswerMessage
                response={response}
                onOpenSource={setOpenCitation}
                activeCitationId={openCitation?.citation_id ?? null}
              />
            )}
          />
        )}
      </main>

      <Footer />

      {openCitation ? (
        <SourceDrawer
          citation={openCitation}
          /* Let the drawer move between citations from the same answer. */
          siblings={
            turns.find((turn) => turn.response?.citations.includes(openCitation))?.response
              ?.citations ?? [openCitation]
          }
          onSelect={setOpenCitation}
          onClose={() => setOpenCitation(null)}
        />
      ) : null}
    </div>,
  );
}
