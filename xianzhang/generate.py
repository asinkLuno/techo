"""Xianzhang — plain ruled notebook sample (2 pages).

Usage: uv run python xianzhang/generate.py
Output: xianzhang/content.tex
"""

from pathlib import Path

HERE = Path(__file__).parent

# ponytail: change for more pages
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
