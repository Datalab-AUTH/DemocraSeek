/**
 * The four onboarding questions.
 *
 * Questions, choices, translations, labels and codes all come from the
 * backend's versioned configuration. This component contains no onboarding
 * wording and no policy fragments of its own.
 */

import { useEffect, useId, useMemo, useRef, useState } from "react";

import type { Dimension, OnboardingConfig, OnboardingUI, Profile, Question } from "../api/types";

interface Props {
  config: OnboardingConfig;
  locale: string;
  initialProfile: Profile | null;
  onComplete: (profile: Profile) => void;
  onCancel?: () => void;
}

type Answers = Partial<Record<Dimension, string>>;

function initialAnswers(profile: Profile | null): Answers {
  if (!profile) return {};
  return {
    role: profile.role_code,
    intent: profile.intent_code,
    support: profile.support_code,
    mode: profile.mode_code,
  };
}

function localizedPresentation(
  config: OnboardingConfig,
  locale: string,
): { questions: Question[]; ui: OnboardingUI } {
  const translation = config.translations.find((item) => item.locale === locale);
  if (!translation) return { questions: config.questions, ui: config.onboarding_ui };

  return {
    ui: translation.ui,
    questions: config.questions.map((question) => {
      const localized = translation.questions[question.id];
      // The backend rejects an incomplete locale. This fallback keeps the UI
      // usable even if an older independently deployed backend is encountered.
      if (!localized) return question;
      return {
        ...question,
        prompt: localized.prompt,
        help_text: localized.help_text,
        choices: question.choices.map((choice) => ({
          ...choice,
          label: localized.choices[choice.code]?.label ?? choice.label,
          description: localized.choices[choice.code]?.description ?? choice.description,
        })),
      };
    }),
  };
}

export function Onboarding({
  config,
  locale,
  initialProfile,
  onComplete,
  onCancel,
}: Props): JSX.Element {
  const presentation = useMemo(
    () => localizedPresentation(config, locale),
    [config, locale],
  );
  const questions = useMemo(
    () => [...presentation.questions].sort((a, b) => a.order - b.order),
    [presentation.questions],
  );
  const ui = presentation.ui;
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Answers>(() => initialAnswers(initialProfile));
  const [error, setError] = useState<string | null>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const errorId = useId();

  const question = questions[step];

  useEffect(() => {
    const heading = headingRef.current;
    const scrollContainer = heading?.closest<HTMLElement>(".app__main");
    if (scrollContainer) scrollContainer.scrollTop = 0;
    heading?.focus({ preventScroll: true });
  }, [step]);

  if (!question) return <p>{ui.no_questions}</p>;

  const selected = answers[question.dimension];
  const isLast = step === questions.length - 1;
  function goNext(): void {
    if (!question) return;
    if (question.required && !answers[question.dimension]) {
      setError(ui.choose_option_error);
      return;
    }
    setError(null);
    if (!isLast) {
      setStep((current) => current + 1);
      return;
    }
    onComplete({
      role_code: answers.role ?? "",
      intent_code: answers.intent ?? "",
      support_code: answers.support ?? "",
      mode_code: answers.mode ?? "",
      policy_version: config.policy_version,
    });
  }

  return (
    <section className="onboarding" aria-labelledby="onboarding-heading" lang={locale}>
      <p className="onboarding__progress" aria-live="polite">
        {ui.progress
          .replace("{current}", String(step + 1))
          .replace("{total}", String(questions.length))}
      </p>

      {/* All four steps at once, with what has been chosen so far. Four blind
          screens in a row leave you unable to see where you are or what you
          picked; this also lets you jump back to fix an earlier answer. */}
      <ol className="stepper">
        {questions.map((item, index) => {
          const chosen = answers[item.dimension];
          const label = chosen
            ? item.choices.find((choice) => choice.code === chosen)?.label
            : null;
          const state = index === step ? "is-current" : chosen ? "is-done" : "is-todo";
          return (
            <li key={item.id} className={`stepper__step ${state}`}>
              <button
                type="button"
                className="stepper__button"
                disabled={index > step && !chosen}
                aria-current={index === step ? "step" : undefined}
                aria-label={`${ui.step_titles[item.dimension]}: ${label ?? ui.not_chosen}`}
                title={label ?? ui.not_chosen}
                onClick={() => {
                  setError(null);
                  setStep(index);
                }}
              >
                <span className="stepper__marker" aria-hidden="true">
                  {chosen && index !== step ? "✓" : index + 1}
                </span>
                <span className="stepper__copy">
                  <span className="stepper__title">{ui.step_titles[item.dimension]}</span>
                  {label ? <span className="stepper__selection">{label}</span> : null}
                </span>
              </button>
            </li>
          );
        })}
      </ol>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          goNext();
        }}
      >
        <fieldset className="onboarding__fieldset">
          <legend>
            <h2 id="onboarding-heading" ref={headingRef} tabIndex={-1}>
              {question.prompt}
            </h2>
          </legend>
          {question.help_text ? (
            <p className="onboarding__help">{question.help_text}</p>
          ) : null}

          {error ? (
            <p className="form-error" id={errorId} role="alert">
              {error}
            </p>
          ) : null}

          <ul className="choices">
            {question.choices.map((choice) => (
              <li key={choice.code}>
                <label className="choice">
                  <input
                    type="radio"
                    name={question.id}
                    value={choice.code}
                    checked={selected === choice.code}
                    aria-describedby={error ? errorId : undefined}
                    onChange={() => {
                      setError(null);
                      setAnswers((current) => ({
                        ...current,
                        [question.dimension]: choice.code,
                      }));
                    }}
                  />
                  <span className="choice__body">
                    <span className="choice__label">{choice.label}</span>
                    {choice.description ? (
                      <span className="choice__description">{choice.description}</span>
                    ) : null}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </fieldset>

        <div className="onboarding__actions">
          {step > 0 ? (
            <button type="button" className="button button--ghost" onClick={() => setStep(step - 1)}>
              {ui.back}
            </button>
          ) : null}
          {onCancel ? (
            <button type="button" className="button button--ghost" onClick={onCancel}>
              {ui.cancel}
            </button>
          ) : null}
          <button type="submit" className="button button--primary">
            {isLast ? ui.finish : ui.next}
          </button>
        </div>
      </form>
    </section>
  );
}
