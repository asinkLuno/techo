"""Green Dot — single page of dot-grid background, no content.

Usage: techo green-dot --size m5|cozyca|a5s|...
"""

from pathlib import Path

from .. import sizes


def content() -> list[str]:
    """Return LaTeX lines for a single empty dot-grid page."""
    return [
        "\\thispagestyle{empty}%",
        "\\null",
        "\\clearpage",
    ]


def generate(size: str) -> None:
    s = sizes.SIZES[size]
    g = sizes.GREEN_DOT[size]
    PW, PH = s["pw"], s["ph"]
    BINDING, RIGHT = g["binding"], g["right_margin"]
    TM, BM = g["top_margin"], g["bottom_margin"]

    sizes.write_sizes_tex()

    out = Path("outputs") / f"green-dot-{size}"
    out.mkdir(parents=True, exist_ok=True)

    # 2-page spread (odd + even)
    full = [*content(), *content()]
    (out / "content.tex").write_text("\n".join(full) + "\n")
    (out / f"green-dot-{size}.tex").write_text(
        f"\\def\\EDITION{{{size}}}%\n"
        f"\\def\\BINDING{{{BINDING}}}%\n"
        f"\\def\\RIGHTMARGIN{{{RIGHT}}}%\n"
        f"\\def\\DTOP{{{TM}}}%\n"
        f"\\def\\DBOT{{{BM}}}%\n"
        f"\\def\\DLEFT{{{BINDING}}}%\n"
        f"\\def\\DRIGHT{{{RIGHT}}}%\n"
        f"\\input{{../../src/green_dot/green-dot.tex}}%\n"
    )
    print(f"Generated {out}/content.tex + green-dot-{size}.tex ({PW}×{PH}mm, 2 pages)")
    sizes.compile(f"green-dot-{size}.tex", out)

    # Spread: 2 pages side-by-side
    spread_tex = (
        "\\documentclass[10pt]{article}\n"
        f"\\usepackage[paperwidth={PW * 2}mm, paperheight={PH}mm, margin=0mm]{{geometry}}\n"
        "\\usepackage{pdfpages}\n"
        "\\begin{document}\n"
        f"\\includepdf[pages={{1,2}}, nup=2x1, width={PW}mm, height={PH}mm]"
        f"{{green-dot-{size}.pdf}}\n"
        "\\end{document}\n"
    )
    (out / "spread.tex").write_text(spread_tex)
    sizes.compile("spread.tex", out)
    print(f"Generated {out}/spread.pdf (spread, {PW * 2}×{PH}mm)")
