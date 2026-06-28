"""Xianzhang — plain ruled notebook generator.

Usage: uv run python xianzhang.py <edition>
  e.g. uv run python xianzhang.py a5s-xianzhang
       uv run python xianzhang.py m5-xianzhang
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
        print(f"Usage: uv run python xianzhang.py <edition>")
        sys.exit(1)
    generate(sys.argv[1])
