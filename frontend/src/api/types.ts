/** Wire types. These mirror the backend Pydantic models in backend/app/schemas. */

export type Dimension = "role" | "intent" | "support" | "mode";

export interface Choice {
  code: string;
  label: string;
  description: string;
  instructions: string[];
}

export interface Question {
  id: string;
  dimension: Dimension;
  order: number;
  required: boolean;
  prompt: string;
  help_text: string;
  choices: Choice[];
}

export interface LocaleOption {
  code: string;
  display_name: string;
  native_name: string;
}

export interface OnboardingUI {
  language_label: string;
  progress: string;
  not_chosen: string;
  choose_option_error: string;
  back: string;
  cancel: string;
  next: string;
  finish: string;
  no_questions: string;
  step_titles: Record<Dimension, string>;
}

export interface LocalizedChoice {
  label: string;
  description: string;
}

export interface LocalizedQuestion {
  prompt: string;
  help_text: string;
  choices: Record<string, LocalizedChoice>;
}

export interface OnboardingTranslation {
  locale: string;
  ui: OnboardingUI;
  questions: Record<string, LocalizedQuestion>;
}

export interface OnboardingConfig {
  policy_version: string;
  default_locale: string;
  locales: LocaleOption[];
  onboarding_ui: OnboardingUI;
  translations: OnboardingTranslation[];
  questions: Question[];
  global_guardrails: string[];
  precedence_note: string;
}

/** The complete stored profile: four codes and the policy version. Nothing else. */
export interface Profile {
  role_code: string;
  intent_code: string;
  support_code: string;
  mode_code: string;
  policy_version: string;
}

/** An image extracted from an approved PDF page. */
export interface Figure {
  figure_id: string;
  document_id: string;
  document_title: string;
  page_number: number;
  caption: string;
  width: number;
  height: number;
  image_url: string;
  source_url: string;
}

export type ExcerptSource = "model_quote_verified" | "chunk_head" | "figure_description";

export interface Citation {
  citation_id: string;
  evidence_id: string;
  document_id: string;
  document_title: string;
  source_type: "internal" | "external";
  authors: string[];
  publishers: string[];
  publication_date: string;
  external_url: string;
  deliverable_id: string;
  page_number: number;
  chunk_id: string;
  supporting_excerpt: string;
  excerpt_source: ExcerptSource;
  source_url: string;
  modality: "text" | "figure";
  /** Images on the cited page. Attached by the backend, never chosen by the model. */
  figures: Figure[];
}

export type AnswerStatus = "grounded" | "insufficient_evidence";

export interface ChatResponse {
  status: AnswerStatus;
  answer: string;
  citations: Citation[];
  policy_version: string;
  request_id: string;
  reason_code: string;
  /** Dominant language detected from this turn's question. */
  language_code: string;
  language_name: string;
  /** English context returned by the stateless API for the next turn. */
  canonical_question: string;
  canonical_answer: string;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
  canonical_content?: string;
  language_code?: string;
  language_name?: string;
}

export interface SourcePage {
  page_number: number;
  text: string;
  truncated: boolean;
  figures: Figure[];
}

export interface SourceResponse {
  document_id: string;
  document_title: string;
  filename: string;
  source_type: "internal" | "external";
  authors: string[];
  publishers: string[];
  external_url: string;
  /** "image" documents are a single picture with no text layer. */
  document_type: "pdf" | "image";
  deliverable_id: string;
  publication_date: string;
  page_count: number;
  corpus_version: string;
  page: SourcePage | null;
  file_url: string | null;
}

export interface CorpusDocument {
  document_id: string;
  document_title: string;
  source_type: "internal" | "external";
  deliverable_id: string;
  page_count: number;
  figure_count: number;
}

export interface CorpusResponse {
  corpus_version: string;
  documents: CorpusDocument[];
  /** Files sitting in the corpus directory that have not been ingested yet. */
  pending_files: string[];
  /** Starter questions derived from indexed headings. */
  suggested_questions: string[];
}
