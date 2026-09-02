/** Renders one assistant turn: the answer, its inline markers and its sources. */

import { useState } from "react";

import type { Citation, ChatResponse, Figure } from "../api/types";
import { formatUi, useUi } from "../i18n";
import { FigureGallery } from "./FigureGallery";

interface Props {
  response: ChatResponse;
  onOpenSource: (citation: Citation) => void;
  /** Citation currently shown in the drawer, so the marker can look active. */
  activeCitationId?: string | null;
}

const MARKER = /(\[C\d+\])/g;

function CopyButton({ text }: { text: string }): JSX.Element {
  const { ui } = useUi();
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="answer__action"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1800);
        } catch {
          /* clipboard unavailable (insecure origin, denied permission) */
        }
      }}
    >
      {copied ? ui.answer.copied : ui.answer.copy}
    </button>
  );
}

export function AnswerMessage({
  response,
  onOpenSource,
  activeCitationId = null,
}: Props): JSX.Element {
  const { ui } = useUi();
  if (response.status === "insufficient_evidence") {
    // Distinguish missing evidence from an unverifiable generated answer.
    const foundButUnusable = response.reason_code === "unverifiable_answer";
    const unavailable = response.reason_code === "generation_unavailable";
    return (
      <div className="answer answer--insufficient" role="note">
        <p className="answer__badge">
          <span aria-hidden="true">⚠</span>{" "}
          {foundButUnusable
            ? ui.answer.unconfirmedTitle
            : unavailable
              ? ui.answer.unavailableTitle
              : ui.answer.insufficientTitle}
        </p>
        <p>
          {foundButUnusable
            ? ui.answer.unconfirmedBody
            : response.answer}
        </p>
        <p className="answer__hint">
          {foundButUnusable
            ? ui.answer.retryDifferent
            : unavailable
              ? ui.answer.retryLater
              : ui.answer.insufficientHint}
        </p>
      </div>
    );
  }

  const byId = new Map(response.citations.map((citation) => [citation.citation_id, citation]));

  // Show each figure once even when several citations share its page.
  const seenFigures = new Set<string>();
  const uniqueFigures: { figure: Figure; citation: Citation }[] = [];
  for (const citation of response.citations) {
    for (const figure of citation.figures) {
      if (seenFigures.has(figure.figure_id)) continue;
      seenFigures.add(figure.figure_id);
      uniqueFigures.push({ figure, citation });
    }
  }

  return (
    <div className="answer">
      {response.answer.split("\n\n").map((paragraph, index) => (
        <p key={index}>
          {paragraph.split(MARKER).map((part, partIndex) => {
            const citation = byId.get(part.replace(/[[\]]/g, ""));
            if (!citation) return <span key={partIndex}>{part}</span>;
            return (
              <button
                key={partIndex}
                type="button"
                className={
                  activeCitationId === citation.citation_id
                    ? "citation-marker citation-marker--active"
                    : "citation-marker"
                }
                onClick={() => onOpenSource(citation)}
                aria-label={formatUi(ui.answer.openSource, {
                  id: citation.citation_id,
                  document: citation.document_title,
                  page: citation.page_number,
                })}
              >
                <span aria-hidden="true">{citation.citation_id}</span>
              </button>
            );
          })}
        </p>
      ))}

      {/* Show each cited figure once per answer. */}
      {uniqueFigures.length > 0 ? (
        <FigureGallery
          figures={uniqueFigures.map((entry) => entry.figure)}
          derived={uniqueFigures.some((entry) => entry.citation.modality === "figure")}
          onOpenSource={(figure) => {
            const owner = uniqueFigures.find(
              (entry) => entry.figure.figure_id === figure.figure_id,
            );
            if (owner) onOpenSource(owner.citation);
          }}
        />
      ) : null}

      {response.citations.length > 0 ? (
        <section className="sources" aria-label={ui.answer.sourcesLabel}>
          <div className="sources__head">
            <div>
              <h3 className="sources__heading">{ui.answer.sourcesTitle}</h3>
              <p className="sources__summary">
                {ui.answer.sourcesSummary}
              </p>
            </div>
            <CopyButton text={response.answer} />
          </div>
          <ol className="sources__list">
            {response.citations.map((citation) => (
              <li key={citation.citation_id}>
                <button
                  type="button"
                  className={
                    activeCitationId === citation.citation_id
                      ? "sources__item sources__item--active"
                      : "sources__item"
                  }
                  onClick={() => onOpenSource(citation)}
                  aria-label={formatUi(ui.answer.viewSource, {
                    id: citation.citation_id,
                    document: citation.document_title,
                    page: citation.page_number,
                  })}
                >
                  <span className="sources__id">{citation.citation_id}</span>
                  <span className="sources__content">
                    <span className="sources__title">
                      {citation.document_title.replace(/_/g, " ")}
                    </span>
                    <span className="sources__meta">
                      {citation.deliverable_id ? `${citation.deliverable_id} · ` : ""}
                      {formatUi(ui.answer.page, { page: citation.page_number })}
                      {/* Match the drawer's source wording. */}
                      {citation.excerpt_source === "model_quote_verified"
                        ? ` · ${ui.answer.exactQuote}`
                        : citation.excerpt_source === "figure_description"
                          ? ` · ${ui.answer.fromImage}`
                          : ` · ${ui.answer.sourceExcerpt}`}
                    </span>
                  </span>
                  {citation.modality === "figure" ? (
                    <span className="sources__tag">{ui.answer.image}</span>
                  ) : null}
                  <svg className="sources__arrow" viewBox="0 0 20 20" aria-hidden="true">
                    <path d="m7 4 6 6-6 6" />
                  </svg>
                </button>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
    </div>
  );
}
