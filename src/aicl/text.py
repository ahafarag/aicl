"""Text segmentation: sections, paragraphs, sentences and word tokens.

Every metric in aicl is computed on the units produced here, so the rules are
kept deliberately simple and documented in docs/measurement_model.md:

- Fenced code blocks and inline code are removed.
- Markdown headings delimit sections and are never counted as sentences.
- Each list item is its own paragraph.
- A word is a run of letters/digits, optionally joined by an apostrophe or
  hyphen ("don't", "state-of-the-art" are one word each).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

WORD_RE = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")

_CODE_FENCE = re.compile(r"^\s*(```|~~~).*?^\s*\1[^\n]*$", re.S | re.M)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_EMPHASIS = re.compile(r"(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_BOUNDARY = re.compile(r"""([.!?…]+["'”’)\]]*)\s+(?=["'“‘(\[]?[^\W_a-z])""")

_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e",
    "fig", "no", "vol", "approx", "inc", "ltd", "co", "cf", "al", "jan", "feb",
    "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
}


@dataclass
class Section:
    title: str | None
    paragraphs: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(self.paragraphs)


def words(text: str) -> list[str]:
    """Lowercased word tokens."""
    return [w.lower() for w in WORD_RE.findall(text)]


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def _clean(text: str) -> str:
    text = _CODE_FENCE.sub("", text)
    text = _INLINE_CODE.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _EMPHASIS.sub(r"\2", text)
    return text.replace("\r\n", "\n")


def parse(text: str) -> list[Section]:
    """Split a document into sections of paragraphs.

    Text before the first heading forms an untitled section. Sections with no
    words are dropped.
    """
    sections = [Section(title=None)]
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            para = " ".join(line.strip() for line in buffer)
            if word_count(para):
                sections[-1].paragraphs.append(para)
            buffer.clear()

    for line in _clean(text).split("\n"):
        heading = _HEADING.match(line)
        if heading:
            flush()
            sections.append(Section(title=heading.group(1)))
        elif not line.strip():
            flush()
        elif _LIST_ITEM.match(line):
            flush()
            buffer.append(_LIST_ITEM.sub("", line))
        else:
            buffer.append(line)
    flush()
    return [s for s in sections if s.paragraphs]


def split_sentences(paragraph: str) -> list[str]:
    """Split one paragraph into sentences, keeping only those with words."""
    sentences = []
    start = 0
    for m in _BOUNDARY.finditer(paragraph):
        if m.group(1).startswith("."):
            last = re.search(r"(\S+)$", paragraph[start:m.start(1)])
            token = last.group(1).lower().lstrip("([\"'“‘") if last else ""
            if token in _ABBREVIATIONS or (len(token) == 1 and token.isalpha()):
                continue
        sentences.append(paragraph[start:m.end(1)].strip())
        start = m.end()
    sentences.append(paragraph[start:].strip())
    return [s for s in sentences if word_count(s)]


def body_text(sections: list[Section]) -> str:
    """Document text without headings, for whole-document word statistics."""
    return "\n\n".join(s.text for s in sections)
