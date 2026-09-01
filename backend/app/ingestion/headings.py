"""Detect headings and derive safe starter-question topics.

PDF text has no layout data, so these rules prefer precision over guessing.
"""

from __future__ import annotations

import re

# Heading detection

# Numbered headings, such as ``3.2 Barriers to participation``.
_NUMBERED = re.compile(r"^\d+(\.\d+){0,3}\.?\s+\S.{0,90}$")
# All-capitals headings.
_ALL_CAPITALS = re.compile(r"^[A-Z][A-Z0-9 ,\-:&/()']{4,90}$")

# Maximum heading length.
MAX_HEADING_WORDS = 14

# Contents entry with dot leaders.
_DOT_LEADER = re.compile(r"\.{4,}")
# Contents entry ending in a page number.
_TRAILING_PAGE_NUMBER = re.compile(r"\s\d{1,4}\s*$")
# Revision-history date row.
_DATE_ROW = re.compile(
    r"^\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}\b",
    re.IGNORECASE,
)
# URL footnote.
_FOOTNOTE_URL = re.compile(r"https?://|www\.", re.IGNORECASE)

# Contents-page detection thresholds.
_CONTENTS_ENTRY_RATIO = 0.3
_MIN_CONTENTS_PAGE_LINES = 6


def is_heading(line: str) -> bool:
    """Return whether a line is a numbered or all-capitals heading."""
    text = line.strip()
    if not text or len(text.split()) > MAX_HEADING_WORDS:
        return False
    if _is_impostor(text):
        return False
    if _NUMBERED.match(text):
        return True
    # Wrapped prose can end mid-thought; headings do not.
    if text.endswith((".", ",", ";", ":")):
        return False
    return bool(_ALL_CAPITALS.match(text)) and any(char.isalpha() for char in text)


def _is_impostor(text: str) -> bool:
    """Heading-shaped lines that come from contents pages, tables and footnotes."""
    return bool(
        _DOT_LEADER.search(text)
        or _TRAILING_PAGE_NUMBER.search(text)
        or _DATE_ROW.match(text)
        or _FOOTNOTE_URL.search(text)
        # Exclude list items and table cells.
        or text.endswith((",", ";"))
    )


def looks_like_contents_page(page_text: str) -> bool:
    """True when most of a page's lines are contents entries."""
    lines = [line.strip() for line in page_text.split("\n") if line.strip()]
    if len(lines) < _MIN_CONTENTS_PAGE_LINES:
        return False
    entries = sum(
        1
        for line in lines
        if _DOT_LEADER.search(line) or _TRAILING_PAGE_NUMBER.search(line)
    )
    return entries / len(lines) >= _CONTENTS_ENTRY_RATIO


def heading_at_or_before(lines: list[str], position: int) -> str:
    """Nearest heading at or above ``position``. Empty string when unknown."""
    for index in range(min(position, len(lines) - 1), -1, -1):
        if is_heading(lines[index]):
            return lines[index].strip()
    return ""


# Topic extraction

# Document sections that are not useful topics.
_FURNITURE = frozenset(
    {
        "contents", "table of contents", "list of figures", "list of tables",
        "references", "bibliography", "annex", "annexes", "appendix", "appendices",
        "acknowledgements", "acknowledgments", "glossary", "abbreviations",
        "disclaimer", "imprint", "index", "notes", "foreword", "preface",
        "document information", "revision history", "version history",
    }
)
# Generic prefixes removed from topic text.
_NOISE_PREFIXES = frozenset(
    {"introduction", "overview", "summary", "background", "conclusion", "conclusions"}
)
# Words that indicate a truncated topic.
_DANGLING_WORDS = frozenset(
    {
        "and", "or", "to", "the", "a", "an", "of", "with", "for", "in", "on",
        "by", "from", "as", "at", "that", "which", "into", "per", "via",
    }
)
# Accepted topic length.
_MIN_TOPIC_WORDS = 2
_MAX_TOPIC_WORDS = 9
# Maximum topics per document.
MAX_TOPICS_PER_DOCUMENT = 6

_LEADING_NUMBER = re.compile(r"^\s*\d+(\.\d+)*\.?\s+")
# Wrapper punctuation, including escaped en and em dashes.
_TRIM_CHARACTERS = " .:-\u2013\u2014"


def clean_topic(heading: str) -> str:
    """Reduce a heading to its subject, or return "" if it has none."""
    text = _LEADING_NUMBER.sub("", heading.strip()).strip(_TRIM_CHARACTERS)
    if not text:
        return ""
    if text.isupper():
        text = text.capitalize()
    if _is_furniture(text):
        return ""
    text = _without_noise_prefix(text)
    return text if _is_usable_subject(text) else ""


def _is_furniture(text: str) -> bool:
    lowered = text.lower()
    if lowered in _FURNITURE:
        return True
    # A furniture prefix also excludes its suffix.
    first_word = re.split(r"[\s:]+", lowered, maxsplit=1)[0]
    return first_word in _FURNITURE


def _without_noise_prefix(text: str) -> str:
    prefix, separator, rest = text.partition(":")
    if separator and prefix.strip().lower() in _NOISE_PREFIXES and rest.strip():
        return rest.strip()
    return text


def _is_usable_subject(text: str) -> bool:
    words = text.split()
    if not (_MIN_TOPIC_WORDS <= len(words) <= _MAX_TOPIC_WORDS):
        return False
    if words[-1].strip(".,;:").lower() in _DANGLING_WORDS:
        return False
    return any(char.isalpha() for char in text)


def extract_topics(page_texts: list[str]) -> list[str]:
    """Return unique, indexed topics in reading order."""
    topics: list[str] = []
    seen: set[str] = set()
    for page_text in page_texts:
        if looks_like_contents_page(page_text):
            continue
        for line in page_text.split("\n"):
            if not is_heading(line):
                continue
            topic = clean_topic(line)
            if not topic or topic.lower() in seen:
                continue
            seen.add(topic.lower())
            topics.append(topic)
            if len(topics) >= MAX_TOPICS_PER_DOCUMENT:
                return topics
    return topics
