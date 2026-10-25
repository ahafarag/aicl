from aicl.text import parse, split_sentences, words


def test_abbreviations_and_initials_do_not_split():
    para = "Dr. Smith met J. R. Jones at 5 p.m. on Monday. They talked, e.g. about rain. Fine!"
    assert split_sentences(para) == [
        "Dr. Smith met J. R. Jones at 5 p.m. on Monday.",
        "They talked, e.g. about rain.",
        "Fine!",
    ]


def test_quotes_and_questions():
    para = 'She asked, "Is it late?" He shrugged. "No."'
    assert split_sentences(para) == ['She asked, "Is it late?"', "He shrugged.", '"No."']


def test_punctuation_only_paragraphs_are_dropped():
    sections = parse("Before the break.\n\n* * *\n\n---\n\nAfter the break.")
    assert sections[0].paragraphs == ["Before the break.", "After the break."]


def test_sections_lists_and_code_are_handled():
    doc = """Intro line one.
Intro line two.

# Part A

- first item
- second item

```python
print("not prose")
```

## Empty

## Part B
Body text here.
"""
    sections = parse(doc)
    assert [s.title for s in sections] == [None, "Part A", "Part B"]
    assert sections[0].paragraphs == ["Intro line one. Intro line two."]
    assert sections[1].paragraphs == ["first item", "second item"]
    assert "print" not in " ".join(s.text for s in sections)


def test_words_keep_contractions_and_hyphens():
    assert words("Don't over-think it, OK?") == ["don't", "over-think", "it", "ok"]
