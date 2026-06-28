"""Xianzhang ruled notebook generator — shared across sizes.

Usage: uv run python xgen.py <edition>
  e.g. uv run python xgen.py a5s
       uv run python xgen.py m5
"""

import sys
from pathlib import Path

TOTAL_PAGES = 2


def generate(edition: str) -> None:
    out = []
    for _ in range(TOTAL_PAGES):
        out.append("\\ruledpage")
        out.append("\\clearpage")
    content = "\n".join(out)
    out_dir = Path(edition)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "content.tex").write_text(content)
    print(f"Generated {out_dir / 'content.tex'} ({TOTAL_PAGES} pages)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: uv run python xgen.py <edition>")
        sys.exit(1)
    generate(sys.argv[1])
