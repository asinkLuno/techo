"""Xianzhang m5 — plain ruled notebook (67×105mm).

Usage: uv run python m5/generate.py
Output: m5/content.tex
"""

from pathlib import Path

HERE = Path(__file__).parent
TOTAL_PAGES = 2


def generate_content() -> str:
    out = []
    for _ in range(TOTAL_PAGES):
        out.append("\\ruledpage")
        out.append("\\clearpage")
    return "\n".join(out)


def main():
    content = generate_content()
    content_path = HERE / "content.tex"
    content_path.write_text(content)
    print(f"Generated {content_path} ({TOTAL_PAGES} pages)")


if __name__ == "__main__":
    main()
