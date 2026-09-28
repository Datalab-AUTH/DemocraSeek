/** Renders one assistant turn: the answer, its inline markers and its sources. */

import { useState } from "react";

import type { Citation, ChatResponse, Figure } from "../api/types";
import { formatUi, type UiCopy, useUi } from "../i18n";
import { FigureGallery } from "./FigureGallery";

interface Props {
  response: ChatResponse;
  onOpenSource: (citation: Citation) => void;
  /** Citation currently shown in the drawer, so the marker can look active. */
  activeCitationId?: string | null;
}

const MARKER = /(\[C\d+\])/g;

/** Explain why there is no answer, using the reason the backend reports. */
function refusalCopy(
  response: ChatResponse,
  ui: UiCopy,
): { title: string; body: string; hint: string } {
  switch (response.reason_code) {
    case "no_relevant_evidence":
      return {
        title: ui.answer.noEvidenceTitle,
        body: ui.answer.noEvidenceBody,
        hint: ui.answer.noEvidenceHint,
      };
    case "model_reported_insufficient":
      return {
        title: ui.answer.notAnsweredTitle,
        body: ui.answer.notAnsweredBody,
        hint: ui.answer.notAnsweredHint,
      };
    case "unverifiable_answer":
      return {
        title: ui.answer.unconfirmedTitle,
        body: ui.answer.unconfirmedBody,
        hint: ui.answer.retryDifferent,
      };
    case "generation_unavailable":
      return {
        title: ui.answer.unavailableTitle,
        body: response.answer,
        hint: ui.answer.retryLater,
      };
    default:
      return {
        title: ui.answer.insufficientTitle,
        body: response.answer,
        hint: ui.answer.insufficientHint,
      };
  }
}

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
    const refusal = refusalCopy(response, ui);
    return (
      <div className="answer answer--insufficient" role="note">
        <p className="answer__badge">
          <span aria-hidden="true">⚠</span> {refusal.title}
        </p>
        <p>{refusal.body}</p>
        <p className="answer__hint">{refusal.hint}</p>
      </div>
    );
  }

  const byId = new Map(response.citations.map((citation) => [citation.citation_id, citation]));

  // Show each figure once even when several citations share its page.
  const seenFigures = new Set<string>();
  const uniqueFigures: { figure: Figure; citation: Citation }[] = [];
  for (const citation of response.citations) {
    if (citation.source_type === "external") continue;
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
                      {citation.source_type === "external" ? (
                        <>
                          {[...citation.publishers, citation.publication_date]
                            .filter(Boolean)
                            .join(" · ")}
                          {` · ${formatUi(ui.answer.page, { page: citation.page_number })}`}
                        </>
                      ) : (
                        <>
                          {citation.deliverable_id ? `${citation.deliverable_id} · ` : ""}
                          {formatUi(ui.answer.page, { page: citation.page_number })}
                          {citation.excerpt_source === "model_quote_verified"
                            ? ` · ${ui.answer.exactQuote}`
                            : citation.excerpt_source === "figure_description"
                              ? ` · ${ui.answer.fromImage}`
                              : ` · ${ui.answer.sourceExcerpt}`}
                        </>
                      )}
                    </span>
                  </span>
                  {citation.source_type === "external" ? (
                    <span className="sources__tag">{ui.answer.externalSource}</span>
                  ) : citation.modality === "figure" ? (
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
