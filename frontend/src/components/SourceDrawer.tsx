/** Citation inspection with a clear evidence-first information hierarchy. */

import { useEffect, useRef, useState } from "react";

import { absoluteUrl, fetchSource } from "../api/client";
import type { Citation, SourceResponse } from "../api/types";
import { formatUi, type UiCopy, useUi } from "../i18n";
import { locateExcerpt } from "../lib/excerpt";
import { FigureGallery } from "./FigureGallery";

interface Props {
  citation: Citation;
  /** Every citation of the same answer, so the reader can compare without reopening. */
  siblings?: Citation[];
  onSelect?: (citation: Citation) => void;
  onClose: () => void;
}

type DrawerView = "evidence" | "page";

interface Provenance {
  tone: "verified" | "figure" | "passage";
  badge: string;
  title: string;
  detail: string;
}

/** Add a client-side page fragment when opening a cited PDF. */
function originalFileHref(source: SourceResponse, pageNumber: number): string | null {
  if (!source.file_url) return null;
  const url = absoluteUrl(source.file_url);
  if (source.document_type === "image") {
    return url;
  }
  if (!Number.isInteger(pageNumber) || pageNumber < 1) {
    return url;
  }
  return `${url}#page=${pageNumber}`;
}

/** A line shorter than this share of a full line ends where the author broke it. */
const SHORT_LINE_RATIO = 0.85;

/** Join the hard-wrapped lines of PDF text; keep blank lines, bullets and short lines. */
function reflowPageText(text: string): string {
  const lines = text.split("\n");
  const lengths = lines.map((line) => line.length).sort((a, b) => a - b);
  const short = (lengths[Math.floor(lengths.length * 0.9)] ?? 0) * SHORT_LINE_RATIO;
  return lines.reduce((out, line, index) => {
    if (index === 0) return line;
    const previous = lines[index - 1] as string;
    const previousIsShort = previous.length < short;
    let join = " ";
    if (!line || !previous) join = "\n";
    else if (previousIsShort && /[.!?]["”’)]?$/.test(previous)) join = "\n\n";
    else if (previousIsShort || /^[•▪◦●–-]\s/.test(line)) join = "\n";
    return out + join + line;
  }, "");
}

function provenance(citation: Citation, ui: UiCopy): Provenance {
  switch (citation.excerpt_source) {
    case "model_quote_verified":
      return {
        tone: "verified",
        badge: ui.source.exactBadge,
        title: ui.source.exactTitle,
        detail: ui.source.exactDetail,
      };
    case "figure_description":
      return {
        tone: "figure",
        badge: ui.source.figureBadge,
        title: ui.source.figureTitle,
        detail: ui.source.figureDetail,
      };
    default:
      return {
        tone: "passage",
        badge: ui.source.passageBadge,
        title: ui.source.passageTitle,
        detail: ui.source.passageDetail,
      };
  }
}

function ChevronIcon({ direction }: { direction: "left" | "right" }): JSX.Element {
  const path = direction === "left" ? "m12.5 4-6 6 6 6" : "m7.5 4 6 6-6 6";
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      <path d={path} />
    </svg>
  );
}

function CloseIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      <path d="m5 5 10 10M15 5 5 15" />
    </svg>
  );
}

function DocumentIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      <path d="M5.5 2.5h6l3 3v12h-9zM11.5 2.5v3h3M8 9h4.5M8 12h4.5" />
    </svg>
  );
}

function ExternalIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      <path d="M11 4h5v5M16 4l-7 7M14 11v4.5H4.5v-10H9" />
    </svg>
  );
}

export function SourceDrawer({
  citation,
  siblings = [],
  onSelect,
  onClose,
}: Props): JSX.Element {
  const { locale, ui } = useUi();
  const [source, setSource] = useState<SourceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<DrawerView>("evidence");
  const closeRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLElement>(null);
  const openerRef = useRef<Element | null>(null);
  const markRef = useRef<HTMLElement>(null);

  useEffect(() => {
    openerRef.current = document.activeElement;
    closeRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
      if (openerRef.current instanceof HTMLElement) openerRef.current.focus();
    };
  }, []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !drawerRef.current) return;
      const focusable = Array.from(
        drawerRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
        ),
      );
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!first || !last) return;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    setSource(null);
    setError(null);
    setView("evidence");
    if (citation.source_type === "external") return undefined;
    fetchSource(citation.source_url)
      .then((result) => {
        if (!cancelled) setSource(result);
      })
      .catch(() => {
        if (!cancelled) setError(ui.source.loadError);
      });
    return () => {
      cancelled = true;
    };
  }, [citation.citation_id, citation.source_url, ui.source.loadError]);

  const said = provenance(citation, ui);
  const isExternal = citation.source_type === "external";
  const position = siblings.findIndex((item) => item.citation_id === citation.citation_id);
  const canNavigate = siblings.length > 1 && position >= 0 && Boolean(onSelect);
  const pageText = reflowPageText(source?.page?.text ?? "");
  const highlight = pageText ? locateExcerpt(pageText, citation.supporting_excerpt) : null;
  const displayTitle = citation.document_title.replace(/_/g, " ");

  function go(step: number): void {
    const next = siblings[(position + step + siblings.length) % siblings.length];
    if (next && onSelect) onSelect(next);
  }

  function showPage(): void {
    setView("page");
    window.requestAnimationFrame(() => {
      markRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
    });
  }

  return (
    <>
      <div className="source-drawer__backdrop" onClick={onClose} aria-hidden="true" />
      <aside
        ref={drawerRef}
        className={`source-drawer${isExternal ? " source-drawer--external" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={formatUi(ui.source.dialog, {
          id: citation.citation_id,
          document: displayTitle,
          page: citation.page_number,
        })}
      >
        <header className="source-drawer__header">
          <div className="source-drawer__topbar">
            <div className="source-drawer__position">
              <span className="source-drawer__citation-id">{citation.citation_id}</span>
              <span>
                {canNavigate
                  ? formatUi(ui.source.sourcePosition, {
                      current: position + 1,
                      total: siblings.length,
                    })
                  : ui.source.answerSource}
              </span>
            </div>

            <div className="source-drawer__header-actions">
              {canNavigate ? (
                <div className="source-drawer__pager" aria-label={ui.source.pager}>
                  <button type="button" onClick={() => go(-1)} aria-label={ui.source.previous}>
                    <ChevronIcon direction="left" />
                  </button>
                  <button type="button" onClick={() => go(1)} aria-label={ui.source.next}>
                    <ChevronIcon direction="right" />
                  </button>
                </div>
              ) : null}
              <button
                ref={closeRef}
                type="button"
                className="source-drawer__close"
                onClick={onClose}
                aria-label={ui.source.close}
              >
                <CloseIcon />
              </button>
            </div>
          </div>

          <div className="source-drawer__title-row">
            <span className="source-drawer__document-icon">
              <DocumentIcon />
            </span>
            <div>
              <p className="source-drawer__eyebrow">{ui.source.source}</p>
              <h2 id="source-drawer-title">{displayTitle}</h2>
            </div>
          </div>

          <div className="source-drawer__metadata" aria-label={ui.source.metadata}>
            {citation.deliverable_id ? <span>{citation.deliverable_id}</span> : null}
            <span>
              {source?.page_count
                ? formatUi(ui.source.pageOf, {
                    page: citation.page_number,
                    total: source.page_count,
                  })
                : formatUi(ui.source.page, { page: citation.page_number })}
            </span>
            <span
              className={`source-drawer__status source-drawer__status--${
                isExternal ? "external" : said.tone
              }`}
            >
              {isExternal || said.tone === "verified" ? (
                <span aria-hidden="true">{isExternal ? "↗" : "✓"}</span>
              ) : null}
              {isExternal ? ui.source.externalBadge : said.badge}
            </span>
          </div>
        </header>

        {!isExternal ? (
          <div className="source-drawer__tabs" role="tablist" aria-label={ui.source.views}>
            <button
              type="button"
              role="tab"
              aria-selected={view === "evidence"}
              className={view === "evidence" ? "source-drawer__tab source-drawer__tab--active" : "source-drawer__tab"}
              onClick={() => setView("evidence")}
            >
              {ui.source.excerptTab}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={view === "page"}
              className={view === "page" ? "source-drawer__tab source-drawer__tab--active" : "source-drawer__tab"}
              onClick={showPage}
              disabled={source?.document_type === "image"}
            >
              {ui.source.fullPageTab}
            </button>
          </div>
        ) : null}

        <div className="source-drawer__body">
          {isExternal ? (
            <div className="source-drawer__view">
              <section className="external-source-card" aria-labelledby="external-source-heading">
                <p className="source-drawer__eyebrow">{ui.source.externalBadge}</p>
                <h3 id="external-source-heading">{ui.source.externalAboutTitle}</h3>
                <p className="external-source-card__lead">{ui.source.externalAboutText}</p>
                <dl className="external-source-card__metadata">
                  <div>
                    <dt>{ui.source.authorsLabel}</dt>
                    <dd>{citation.authors.join(", ")}</dd>
                  </div>
                  <div>
                    <dt>{ui.source.publishersLabel}</dt>
                    <dd>{citation.publishers.join(", ")}</dd>
                  </div>
                  <div>
                    <dt>{ui.source.publishedLabel}</dt>
                    <dd>{citation.publication_date}</dd>
                  </div>
                  <div>
                    <dt>{ui.source.pageLabel}</dt>
                    <dd>{citation.page_number}</dd>
                  </div>
                </dl>
              </section>
            </div>
          ) : view === "evidence" ? (
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
                <blockquote className="evidence-card__quote">
                  {citation.supporting_excerpt}
                </blockquote>
                <div className={`evidence-card__proof evidence-card__proof--${said.tone}`}>
                  <span className="evidence-card__proof-icon" aria-hidden="true">
                    {said.tone === "verified" ? "✓" : said.tone === "figure" ? "▧" : "i"}
                  </span>
                  <div>
                    <strong>{said.title}</strong>
                    <p>{said.detail}</p>
                    {/* The corpus is in English; quotes stay verbatim. */}
                    {locale !== "en" && said.tone !== "figure" ? (
                      <p>{ui.source.originalLanguage}</p>
                    ) : null}
                  </div>
                </div>
                {source?.document_type !== "image" ? (
                  <button type="button" className="evidence-card__context" onClick={showPage}>
                    {ui.source.seeOnPage}
                    <ChevronIcon direction="right" />
                  </button>
                ) : null}
              </section>

              {citation.figures.length > 0 ? (
                <section className="source-drawer__section" aria-label={ui.source.figureSection}>
                  <div className="source-drawer__section-heading">
                    <p className="source-drawer__eyebrow">{ui.source.imageFromPage}</p>
                    <h3>{formatUi(ui.source.imageOnPage, { page: citation.page_number })}</h3>
                  </div>
                  <FigureGallery
                    figures={citation.figures}
                    derived={citation.modality === "figure"}
                  />
                </section>
              ) : null}

              {error ? (
                <p className="form-error" role="alert">
                  {error}
                </p>
              ) : null}
              {!source && !error ? (
                <div className="source-drawer__loading" role="status">
                  <span aria-hidden="true" /> {ui.source.loadingDetails}
                </div>
              ) : null}

            </div>
          ) : (
            <div className="source-drawer__view" role="tabpanel">
              <section className="page-context" aria-labelledby="page-context-heading">
                <div className="page-context__heading">
                  <div>
                    <p className="source-drawer__eyebrow">{ui.source.textFromSource}</p>
                    <h3 id="page-context-heading">
                      {source?.page_count
                        ? formatUi(ui.source.pageOf, {
                            page: citation.page_number,
                            total: source.page_count,
                          })
                        : formatUi(ui.source.page, { page: citation.page_number })}
                    </h3>
                  </div>
                  {highlight ? (
                    <span className="page-context__highlight-key">{ui.source.highlighted}</span>
                  ) : null}
                </div>

                {!source && !error ? (
                  <div className="source-drawer__loading" role="status">
                    <span aria-hidden="true" /> {ui.source.loadingText}
                  </div>
                ) : null}
                {error ? (
                  <p className="form-error" role="alert">
                    {error}
                  </p>
                ) : null}
                {source?.document_type === "image" ? (
                  <p className="source-drawer__note">
                    {ui.source.imageNoText}
                  </p>
                ) : null}
                {source?.document_type !== "image" && source?.page ? (
                  <article className="page-context__paper">
                    {pageText ? (
                      <p className="page-context__text">
                        {highlight ? (
                          <>
                            {highlight.before}
                            <mark className="page-context__mark" ref={markRef}>
                              {highlight.match}
                            </mark>
                            {highlight.after}
                          </>
                        ) : (
                          pageText
                        )}
                      </p>
                    ) : (
                      <p className="source-drawer__note">
                        {ui.source.noReadableText}
                      </p>
                    )}
                  </article>
                ) : null}
                {source?.page?.truncated ? (
                  <p className="source-drawer__note">
                    {ui.source.truncated}
                  </p>
                ) : null}
              </section>
            </div>
          )}
        </div>

        <footer className="source-drawer__footer">
          <button type="button" className="button button--ghost" onClick={onClose}>
            {ui.source.back}
          </button>
          {isExternal && citation.external_url ? (
            <a
              className="button button--primary source-drawer__original"
              href={citation.external_url}
              target="_blank"
              rel="noreferrer noopener"
            >
              {ui.source.visitExternal}
              <ExternalIcon />
            </a>
          ) : source && originalFileHref(source, citation.page_number) ? (
            <a
              className="button button--primary source-drawer__original"
              href={originalFileHref(source, citation.page_number) ?? undefined}
              target="_blank"
              rel="noreferrer noopener"
            >
              {source.document_type === "image"
                ? ui.source.openOriginalImage
                : ui.source.openOriginalPdf}
              <ExternalIcon />
            </a>
          ) : (
            <button type="button" className="button button--primary" disabled>
              {ui.source.loadingOriginal}
            </button>
          )}
        </footer>
      </aside>
    </>
  );
}
