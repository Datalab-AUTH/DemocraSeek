/** Simple guidance shown before the first question. */

import type { CorpusDocument } from "../api/types";
import { branding } from "../branding";
import { formatUi, useUi } from "../i18n";

interface Props {
  documents: CorpusDocument[];
  /** Curated starter questions keyed by interface locale. */
  exampleQuestions: Record<string, string[]>;
  pendingFiles: string[];
  onPickExample: (question: string) => void;
}

export function EmptyState({
  documents,
  exampleQuestions,
  pendingFiles,
  onPickExample,
}: Props): JSX.Element {
  const { locale, ui } = useUi();
  // Every locale carries the full list (the backend refuses incomplete files),
  // so this fallback only matters if the API and the UI disagree on locales.
  const localizedQuestions = exampleQuestions[locale] ?? exampleQuestions.en ?? [];
  return (
    <div className="empty">
      <div className="empty__hero">
        <span className="empty__eyebrow">{ui.empty.eyebrow}</span>
        <h2>{ui.empty.title}</h2>
        <p className="empty__lead">
          {formatUi(ui.empty.lead, { project: branding.projectName })}
        </p>
      </div>

      {documents.length === 0 ? (
        <p className="empty__warning" role="status">
          {ui.empty.libraryNotReady}
        </p>
      ) : null}

      {pendingFiles.length > 0 ? (
        <p className="empty__warning" role="status">
          {ui.empty.pendingMaterial}
        </p>
      ) : null}

      {localizedQuestions.length > 0 ? (
        <section className="empty__examples" aria-labelledby="examples-heading">
          <h3 id="examples-heading">{ui.empty.examplesTitle}</h3>
          <div className="empty__chips">
            {localizedQuestions.map((question) => (
              <button
                key={question}
                type="button"
                className="chip"
                onClick={() => onPickExample(question)}
              >
                <span className="chip__icon" aria-hidden="true">
                  ↗
                </span>
                {question}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <div className="empty__scope" role="note">
        <svg
          className="empty__scope-icon"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          aria-hidden="true"
          focusable="false"
        >
          <circle cx="10" cy="10" r="8.2" />
          <path d="M10 9.2v4.9" />
          <circle cx="10" cy="6.3" r="0.6" fill="currentColor" />
        </svg>
        <p>{formatUi(ui.empty.scope, { project: branding.projectName })}</p>
      </div>
    </div>
  );
}
