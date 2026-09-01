/**
 * Locating a cited excerpt inside the full page text.
 *
 * The drawer shows the quote and then the page it came from. Highlighting the
 * quote in place is the difference between asking a reader to trust the system
 * and letting them check it: they see the sentence sitting in its own paragraph,
 * on the page the citation names.
 *
 * Matching has to tolerate whitespace, because the excerpt is stored with its
 * spacing collapsed while the page keeps the line breaks that PDF extraction
 * produced. It also has to tolerate a trailing ellipsis, which the backend adds
 * when an excerpt is the opening of a longer passage.
 *
 * Verified against the real corpus: every excerpt of all three kinds
 * (verified quote, passage opening, figure caption) was found in its page.
 * When a match cannot be found the drawer simply shows the page unhighlighted -
 * never a wrong highlight, which would be worse than none.
 */

export interface ExcerptMatch {
  before: string;
  match: string;
  after: string;
}

interface Normalised {
  text: string;
  /** For each character of `text`, its index in the original string. */
  origin: number[];
}

/** Collapse whitespace runs to one space, remembering where each character came from. */
function normalise(text: string): Normalised {
  const chars: string[] = [];
  const origin: number[] = [];
  let inSpace = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index] as string;
    if (/\s/.test(char)) {
      if (!inSpace && chars.length > 0) {
        chars.push(" ");
        origin.push(index);
        inSpace = true;
      }
    } else {
      chars.push(char);
      origin.push(index);
      inSpace = false;
    }
  }
  return { text: chars.join(""), origin };
}

/** Excerpts that open a longer passage end in an ellipsis the page does not have. */
function trimTail(excerpt: string): string {
  return excerpt.replace(/\s*(\.\.\.|…)\s*$/, "").trim();
}

/** Too short to be a safe match: a common phrase would highlight the wrong place. */
const MIN_MATCH_CHARS = 16;

/**
 * Longest opening of `needle` that appears in `haystack`, cut at word boundaries.
 *
 * An excerpt can diverge from the page anywhere - a truncated quote, a word that
 * extraction hyphenated differently - so a fixed-length fallback misses whenever
 * the divergence comes early. Walking back one word at a time always highlights
 * as much as genuinely matches, and never less.
 */
function longestPrefixMatch(haystack: string, needle: string): { at: number; length: number } | null {
  const words = needle.split(" ");
  for (let count = words.length; count > 0; count -= 1) {
    const prefix = words.slice(0, count).join(" ");
    if (prefix.length < MIN_MATCH_CHARS) return null;
    const at = haystack.indexOf(prefix);
    if (at >= 0) return { at, length: prefix.length };
  }
  return null;
}

export function locateExcerpt(pageText: string, excerpt: string): ExcerptMatch | null {
  const needleSource = trimTail(excerpt);
  if (needleSource.length < MIN_MATCH_CHARS || pageText.length === 0) return null;

  const page = normalise(pageText);
  const needle = normalise(needleSource).text;
  if (needle.length < MIN_MATCH_CHARS) return null;

  const hit = longestPrefixMatch(page.text, needle);
  if (!hit) return null;
  const { at, length } = hit;

  const start = page.origin[at] as number;
  const end = page.origin[at + length - 1] as number;
  return {
    before: pageText.slice(0, start),
    match: pageText.slice(start, end + 1),
    after: pageText.slice(end + 1),
  };
}
