---
title: "Ingestion pipeline"
doc_type: reference
layer: architecture
audience: "developer or corpus operator"
reader_goal: "understand and verify how approved files become searchable evidence"
reader_state: "knows the system overview"
source_of_truth: true
status: stable
canonical_sources:
  - "backend/app/ingestion/pipeline.py"
  - "backend/app/cli.py"
  - "backend/app/corpus/registry.py"
related_docs:
  - "docs/operations/corpus-management.md"
  - "docs/architecture/retrieval-and-data.md"
rag_index: true
---

# Ingestion pipeline

Ingestion is an offline, operator-triggered pipeline implemented in
`backend/app/ingestion/pipeline.py`.

## End-to-end sequence

```text
1. discover approved files
2. read optional metadata
3. derive stable document identity
4. compute file checksum and index fingerprint
5. skip unchanged documents
6. extract page text or load a standalone image
7. clean page text and detect review conditions
8. detect headings and skip contents pages
9. create page-scoped text chunks
10. extract, filter, caption, and store figures
11. use the VLM to create searchable figure descriptions
12. create embeddings for all chunks
13. replace the document's rows in pgvector
14. save registry records
15. save a JSON and text ingestion report
```

## File discovery and approval boundary

Supported approved files:

- `.pdf`;
- `.png`;
- `.jpg` / `.jpeg`;
- `.webp`;
- `.bmp`;
- `.tif` / `.tiff`;
- `.gif`.

The operator separates them under `CORPUS_PATH`, normally:

```text
data/corpus/
|-- internal/   # INNOVADE material that the interface may open
|-- external/   # searchable local copies that the interface never exposes
`-- corpus.metadata.yaml
```

No browser upload endpoint exists. External sources require a reviewed title,
authors, publishers, publication date, and absolute HTTP(S) URL in
`corpus.metadata.yaml`. Incomplete external metadata fails closed for that file.
Internal metadata is optional. Title precedence is operator metadata, embedded
PDF title, then filename.

The external PDF is used only during ingestion, retrieval, generation, and
citation validation. Its file, page text, excerpts, and extracted figures are
not served to the browser. A cited external source instead shows its authors,
publisher, publication date, cited page, and a link to the reviewed URL.

## Stable identity, checksum, and fingerprint

The filename is normalized into a stable `document_id`. SHA-256 identifies the
file contents. The index fingerprint identifies how the project transformed the
file:

```text
embedding provider
| embedding model
| embedding dimensions
| chunk size
| chunk overlap
| INDEX_VERSION
| vision provider:model
| CHUNKING_VERSION
```

A document is skipped only when its checksum, index fingerprint, and source
metadata fingerprint match the registry. Therefore changing a title, author,
publisher, date, URL, or internal/external folder is applied by the next normal
incremental ingestion. This also prevents incompatible vectors from being mixed.

## Page extraction

`pypdf` produces one `PageText` record per PDF page. Page numbers are 1-based
and retained all the way to the citation API. A chunk never crosses a page
boundary; this is the key property that makes exact page citations possible.

A standalone image becomes a one-page document with one figure and no extracted
text layer.

## Empty pages and OCR-review detection

The extractor flags pages with no extractable text and pages with images but
very little text. The ingestion report lists them for human review.

This is detection, not OCR. The current pipeline does not use Tesseract,
PaddleOCR, MinerU, Docling, or another OCR engine. A scanned text page can
therefore be visible as an image without its text becoming searchable.

## Cleaning

Repeated headers, repeated footers, and isolated page numbers are removed while
page identity is preserved. Cleaning reduces noisy retrieval without rewriting
the document's substantive text.

## Contents pages and headings

Likely table-of-contents pages are not chunked because dot leaders and heading
lists can outrank real prose. Heading detection is heuristic and also supplies
topics used for starter questions. It is not a full document-layout model.

## Text chunking

Each cleaned page is split using the configured character size and overlap:

```dotenv
CHUNK_SIZE=1200
CHUNK_OVERLAP=180
```

Every chunk receives deterministic metadata including document ID, page number,
chunk ID, checksum, corpus/index versions, and embedding identity. Deterministic
IDs make repeated ingestion idempotent.

## Figure extraction and filtering

For each PDF page, `pypdf` exposes embedded raster images. DemocraSeek decodes
them and rejects likely logos, bullets, rules, and page furniture.

Current filters:

- both dimensions must be at least 100 px;
- area must be at least 20,000 px;
- maximum aspect ratio is 20:1;
- an identical image appearing on three or more pages is treated as decoration;
- at most eight candidate figures are retained per page;
- stored images are downscaled to a maximum long side of 1,400 px.

Accepted images are normalized to deterministic PNG files.

This does not rasterize arbitrary vector drawings. A chart drawn entirely as PDF
vector primitives may not be extracted.

## Caption association

The cleaned page text is checked for English lines beginning with labels such as
`Figure`, `Fig.`, `Table`, `Chart`, `Diagram`, `Image`, or `Graph`. Additional
guards reject body paragraphs that merely begin with a similar word.

Captions and kept images are associated by order of appearance on the same page.
This is a heuristic, not spatial layout analysis. It can be wrong on a complex
multi-column page.

## Vision description and figure chunks

When `VISION_PROVIDER=openai_compatible`, the VLM receives each stored image and
its caption once during ingestion. Caption plus generated description become a
figure chunk. Its metadata explicitly says:

- `modality=figure`;
- whether the description is VLM-derived or caption-only;
- the exact document and page;
- the linked figure ID.

When vision is disabled, a captioned figure can still become searchable by its
document caption. The application must not claim that it has read visual content
in that mode.

## Embedding

Text and figure chunks are sent in batches to the embedding endpoint. The
configured model returns a 768-dimensional vector for each chunk. A dimension
mismatch fails loudly.

## Vector replacement

For an updated document, the vector store deletes that document's old rows,
embeds the new chunks, and upserts the new rows. Replacement prevents orphaned
chunks when a document becomes shorter.

The PostgreSQL rows and JSON registry are not one distributed transaction. JSON
writes are atomic at the file level and ingestion is single-writer, but a process
failure between stores may require rerunning ingestion. The checksum/fingerprint
model makes that recovery deterministic.

## Registry and report

After vector replacement, the pipeline stores:

- document registry record;
- cleaned page records;
- figure records and PNG paths;
- ingestion outcome and warnings.

Every run writes both machine-readable JSON and human-readable text reports.
Reports are audit artifacts; they are not used for retrieval.

## Idempotency, removals, and concurrency

`ingest`, `remove`, and `reindex` take one writer lock on the index location.
A second writer is refused instead of racing over the registry.

Unchanged documents are skipped. Updated documents are replaced. Files removed
from the corpus are removed during a full corpus scan. `--only` intentionally
does not infer removals outside the selected file.

---
