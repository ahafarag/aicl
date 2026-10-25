import json
from pathlib import Path

from aicl.cli import main

EXAMPLES = Path(__file__).parent.parent / "examples"


def test_summary(capsys):
    assert main(["analyze", str(EXAMPLES / "draft.md")]) == 0
    out = capsys.readouterr().out
    assert "Sentence length, CV" in out
    assert "not a test of authorship" in out


def test_compare_json(capsys):
    main(["analyze", str(EXAMPLES / "draft.md"), "--compare", str(EXAMPLES / "edited.md"), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert set(data) == {"before", "after"}
    assert data["before"]["stock_phrases"]["per_1k_words"] > data["after"]["stock_phrases"]["per_1k_words"]
