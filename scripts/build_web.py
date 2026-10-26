"""Assemble the static site in web/dist (for a static Hugging Face Space or GitHub Pages).

    python scripts/build_web.py
"""

import shutil
from pathlib import Path

WEB = Path("web")
DIST = WEB / "dist"
FILES = ["index.html", "app.js", "aicl.js", "extract.js", "lm.js", "worker.js", "README.md"]


def main() -> None:
    # Empty dist rather than deleting it: Windows refuses to remove a directory that a
    # local preview server is running in.
    DIST.mkdir(parents=True, exist_ok=True)
    for child in DIST.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    (DIST / "examples").mkdir()
    for name in FILES:
        shutil.copy2(WEB / name, DIST / name)
    for example in (WEB / "examples").glob("*.txt"):
        shutil.copy2(example, DIST / "examples" / example.name)
    shutil.copy2("src/aicl/data/reference_liang.json", DIST / "reference.json")
    print(f"Built {DIST} ({sum(1 for _ in DIST.rglob('*') if _.is_file())} files)")


if __name__ == "__main__":
    main()
