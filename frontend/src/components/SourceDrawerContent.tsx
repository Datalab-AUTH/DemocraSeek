import type { RefObject } from "react";

import type { Citation, SourceResponse } from "../api/types";
import { formatUi, type UiCopy } from "../i18n";
import { locateExcerpt } from "../lib/excerpt";
import { FigureGallery } from "./FigureGallery";

export interface Provenance {
  tone: "verified" | "figure" | "passage";
  badge: string;
  title: string;
  detail: string;
}

interface Props {
  citation: Citation;
  source: SourceResponse | null;
  error: string | null;
  view: "evidence" | "page";
  said: Provenance;
  ui: UiCopy;
  markRef: RefObject<HTMLElement>;
  onShowPage: () => void;
}

function ChevronIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      <path d="m7.5 4 6 6-6 6" />
    </svg>
  );
}

export function SourceDrawerContent({
  citation,
  source,
  error,
  view,
  said,
  ui,
  markRef,
  onShowPage,
}: Props): JSX.Element {
  if (citation.source_type === "external") {
    return (
      <div className="source-drawer__view">
        <section className="external-source-card" aria-labelledby="external-source-heading">
          <p className="source-drawer__eyebrow">{ui.source.externalBadge}</p>
          <h3 id="external-source-heading">{ui.source.externalAboutTitle}</h3>
          <p className="external-source-card__lead">{ui.source.externalAboutText}</p>
          <dl className="external-source-card__metadata">
            <div><dt>{ui.source.authorsLabel}</dt><dd>{citation.authors.join(", ")}</dd></div>
            <div><dt>{ui.source.publishersLabel}</dt><dd>{citation.publishers.join(", ")}</dd></div>
            <div><dt>{ui.source.publishedLabel}</dt><dd>{citation.publication_date}</dd></div>
            <div><dt>{ui.source.pageLabel}</dt><dd>{citation.page_number}</dd></div>
          </dl>
        </section>
      </div>
    );
  }

  if (view === "evidence") {
    return (
      <div className="source-drawer__view" role="tabpanel">
        <section className="evidence-card" aria-labelledby="evidence-heading">
          <div className="evidence-card__heading">
            <div>
              <p className="source-drawer__eyebrow">{ui.source.whyShown}</p>
              <h3 id="evidence-heading">{ui.source.excerptHeading}</h3>
            </div>
            <span className={`evidence-card__badge evidence-card__badge--${said.tone}`}>
              {said.badge}
            </span>
          </div>
          <blockquote className="evidence-card__quote">{citation.supporting_excerpt}</blockquote>
          <div className={`evidence-card__proof evidence-card__proof--${said.tone}`}>
            <span className="evidence-card__proof-icon" aria-hidden="true">
              {said.tone === "verified" ? "✓" : said.tone === "figure" ? "▧" : "i"}
            </span>
            <div><strong>{said.title}</strong><p>{said.detail}</p></div>
          </div>
          {source?.document_type !== "image" ? (
            <button type="button" className="evidence-card__context" onClick={onShowPage}>
              {ui.source.seeOnPage}<ChevronIcon />
            </button>
          ) : null}
        </section>

        {citation.figures.length > 0 ? (
          <section className="source-drawer__section" aria-label={ui.source.figureSection}>
            <div className="source-drawer__section-heading">
              <p className="source-drawer__eyebrow">{ui.source.imageFromPage}</p>
              <h3>{formatUi(ui.source.imageOnPage, { page: citation.page_number })}</h3>
            </div>
            <FigureGallery figures={citation.figures} derived={citation.modality === "figure"} />
          </section>
        ) : null}

        {error ? <p className="form-error" role="alert">{error}</p> : null}
        {!source && !error ? (
          <div className="source-drawer__loading" role="status">
            <span aria-hidden="true" /> {ui.source.loadingDetails}
          </div>
        ) : null}
      </div>
    );
  }

  const pageText = source?.page?.text ?? "";
  const highlight = pageText ? locateExcerpt(pageText, citation.supporting_excerpt) : null;
  return (
    <div className="source-drawer__view" role="tabpanel">
      <section className="page-context" aria-labelledby="page-context-heading">
        <div className="page-context__heading">
          <div>
            <p className="source-drawer__eyebrow">{ui.source.textFromSource}</p>
            <h3 id="page-context-heading">
              {source?.page_count
                ? formatUi(ui.source.pageOf, { page: citation.page_number, total: source.page_count })
                : formatUi(ui.source.page, { page: citation.page_number })}
            </h3>
          </div>
          {highlight ? <span className="page-context__highlight-key">{ui.source.highlighted}</span> : null}
        </div>
        {!source && !error ? (
          <div className="source-drawer__loading" role="status"><span aria-hidden="true" /> {ui.source.loadingText}</div>
        ) : null}
        {error ? <p className="form-error" role="alert">{error}</p> : null}
        {source?.document_type === "image" ? <p className="source-drawer__note">{ui.source.imageNoText}</p> : null}
        {source?.document_type !== "image" && source?.page ? (
          <article className="page-context__paper">
            {pageText ? (
              <p className="page-context__text">
                {highlight ? <>{highlight.before}<mark className="page-context__mark" ref={markRef}>{highlight.match}</mark>{highlight.after}</> : pageText}
              </p>
            ) : <p className="source-drawer__note">{ui.source.noReadableText}</p>}
          </article>
        ) : null}
        {source?.page?.truncated ? <p className="source-drawer__note">{ui.source.truncated}</p> : null}
      </section>
    </div>
  );
}
