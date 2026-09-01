/**
 * The conversation.
 *
 * The composer is pinned to the bottom of the panel and the history scrolls
 * above it. Previously the composer sat at the end of a growing page, so the
 * thing you need on every turn walked off the screen as you used the app.
 */

import { useEffect, useRef, useState } from "react";

import { sendQuestion } from "../api/client";
import type { ChatResponse, Citation, ConversationMessage, Profile } from "../api/types";
import { useUi } from "../i18n";

export interface Turn {
  question: string;
  response: ChatResponse | null;
}

interface Props {
  profile: Profile;
  turns: Turn[];
  onTurnsChange: (turns: Turn[]) => void;
  renderAnswer: (response: ChatResponse) => JSX.Element;
  renderEmpty: (onPick: (question: string) => void) => JSX.Element;
  onOpenSource?: (citation: Citation) => void;
  maxQuestionChars?: number;
}

export function ChatPanel({
  profile,
  turns,
  onTurnsChange,
  renderAnswer,
  renderEmpty,
  maxQuestionChars = 2000,
}: Props): JSX.Element {
  const { ui } = useUi();
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, pending]);

  function pickExample(question: string): void {
    setDraft(question);
    inputRef.current?.focus();
  }

  async function submit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    const question = draft.trim();
    if (!question || pending) return;

    const history: ConversationMessage[] = turns.flatMap((turn) =>
      turn.response
        ? [
            {
              role: "user" as const,
              content: turn.question,
              canonical_content: turn.response.canonical_question,
              language_code: turn.response.language_code,
              language_name: turn.response.language_name,
            },
            {
              role: "assistant" as const,
              content: turn.response.answer,
              canonical_content: turn.response.canonical_answer,
              language_code: turn.response.language_code,
              language_name: turn.response.language_name,
            },
          ]
        : [],
    );

    setDraft("");
    setError(null);
    setPending(true);
    onTurnsChange([...turns, { question, response: null }]);

    try {
      const response = await sendQuestion(question, profile, history);
      onTurnsChange([...turns, { question, response }]);
    } catch {
      setError(ui.chat.error);
      onTurnsChange(turns);
      setDraft(question);
    } finally {
      setPending(false);
      inputRef.current?.focus();
    }
  }

  const canSend = draft.trim().length > 0 && !pending;

  return (
    <section className="chat" aria-label={ui.chat.conversation}>
      <div className="chat__history">
        {turns.length === 0 && !pending ? renderEmpty(pickExample) : null}

        {turns.map((turn, index) => (
          <article key={index} className="turn">
            <div className="turn__question">
              <span className="turn__avatar turn__avatar--user" aria-hidden="true">
                {ui.chat.you}
              </span>
              <p>{turn.question}</p>
            </div>
            {turn.response ? (
              <div className="turn__answer">
                <span className="turn__avatar turn__avatar--app" aria-hidden="true">
                  DS
                </span>
                <div className="turn__answer-body">{renderAnswer(turn.response)}</div>
              </div>
            ) : null}
          </article>
        ))}

        <div aria-live="polite" aria-atomic="true" className="chat__status">
          {pending ? ui.chat.finding : ""}
        </div>
        <div ref={endRef} />
      </div>

      <div className="composer">
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}

        <form onSubmit={submit}>
          <label className="visually-hidden" htmlFor="question-input">
            {ui.chat.questionLabel}
          </label>
          <div className="composer__box">
            <textarea
              id="question-input"
              ref={inputRef}
              className="composer__input"
              value={draft}
              rows={1}
              maxLength={maxQuestionChars}
              placeholder={ui.chat.placeholder}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                // Enter sends, Shift+Enter starts a new line: the convention
                // people already have from every other chat interface.
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submit(event);
                }
              }}
            />
            <button type="submit" className="button button--primary composer__submit" disabled={!canSend}>
              <span>{pending ? ui.chat.working : ui.chat.ask}</span>
              <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
                <path d="m4 10 11-6-3.2 12-2.2-4.1L4 10Z" />
                <path d="m9.6 11.9 2.1-2.4" />
              </svg>
            </button>
          </div>
          {draft.length >= Math.floor(maxQuestionChars * 0.8) ? (
            <span className="composer__counter">
              {draft.length} / {maxQuestionChars}
            </span>
          ) : null}
        </form>
      </div>
    </section>
  );
}
