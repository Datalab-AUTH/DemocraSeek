/**
 * What a user sees before their first question.
 *
 * The first screen is intentionally light: it tells a visitor what they can do
 * without exposing document inventory or ingestion details meant for operators.
 */

import type { CorpusDocument } from "../api/types";
import { branding } from "../branding";
import { formatUi, localizeExamples, useUi } from "../i18n";

interface Props {
  documents: CorpusDocument[];
  exampleQuestions: string[];
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
  const localizedQuestions = localizeExamples(locale, exampleQuestions);
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
    </div>
  );
}
