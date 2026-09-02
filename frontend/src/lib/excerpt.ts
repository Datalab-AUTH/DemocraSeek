/** Locate a citation excerpt in page text despite whitespace differences. */

export interface ExcerptMatch {
  before: string;
  match: string;
  after: string;
}

interface Normalised {
  text: string;
  /** Original index for each normalized character. */
  origin: number[];
}

/** Collapse whitespace while retaining original indices. */
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

/** Remove an artificial trailing ellipsis. */
function trimTail(excerpt: string): string {
  return excerpt.replace(/\s*(\.\.\.|…)\s*$/, "").trim();
}

/** Minimum length for an unambiguous highlight. */
const MIN_MATCH_CHARS = 16;

/** Find the longest word-aligned opening of ``needle`` in ``haystack``. */
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
