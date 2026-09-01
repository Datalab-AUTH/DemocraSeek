/**
 * Images from cited pages.
 *
 * A figure appears here because a validated citation points at its page. When
 * vision is enabled, its searchable description was produced during ingestion;
 * the original image remains visible so the reader can check that description.
 */

import { absoluteUrl } from "../api/client";
import type { Figure } from "../api/types";
import { formatUi, useUi } from "../i18n";

interface Props {
  figures: Figure[];
  /** True when the answer relies on what the figure shows, not just its page. */
  derived?: boolean;
  onOpenSource?: (figure: Figure) => void;
}

export function FigureGallery({ figures, derived = false, onOpenSource }: Props): JSX.Element | null {
  const { ui } = useUi();
  if (figures.length === 0) return null;

  return (
    <figure className="figures" aria-label={ui.figures.label}>
      <div className="figures__grid">
        {figures.map((figure) => (
          <button
            key={figure.figure_id}
            type="button"
            className="figures__item"
            onClick={() => onOpenSource?.(figure)}
            aria-label={
              figure.caption
                ? `${figure.caption} — ${formatUi(ui.figures.fromDocument, {
                    document: figure.document_title,
                    page: figure.page_number,
                  })}`
                : formatUi(ui.figures.figureFrom, {
                    document: figure.document_title,
                    page: figure.page_number,
                  })
            }
          >
            <img
              src={absoluteUrl(figure.image_url)}
              alt={
                figure.caption ||
                formatUi(ui.figures.figureFrom, {
                  document: figure.document_title,
                  page: figure.page_number,
                })
              }
              loading="lazy"
              width={figure.width}
              height={figure.height}
            />
          </button>
        ))}
      </div>
      <figcaption className="figures__caption">
        {figures.length === 1 && figures[0]?.caption ? (
          <strong>{figures[0].caption}</strong>
        ) : null}
        <span className="figures__origin">
          {figures.length === 1
            ? formatUi(ui.figures.fromDocument, {
                document: figures[0]?.document_title ?? "",
                page: figures[0]?.page_number ?? "",
              })
            : formatUi(ui.figures.multiple, { count: figures.length })}
        </span>
        {derived ? (
          <span className="figures__derived">
            <span aria-hidden="true">👁</span> {ui.figures.derived}
          </span>
        ) : null}
      </figcaption>
    </figure>
  );
}
