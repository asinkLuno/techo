"""Green Dot — single page of dot-grid background, no content.

Usage: techo green-dot --size m5|cozyca|a5s|...
"""

from .. import build, sizes


def content() -> list[str]:
    """Return LaTeX lines for a single empty dot-grid page."""
    return [
        "\\thispagestyle{empty}%",
        "\\null",
        "\\clearpage",
    ]


def generate(size: str) -> None:
    s = sizes.SIZES[size]
    g = sizes.green_dot(size)
    PW, PH = s["pw"], s["ph"]
    BINDING, RIGHT = g["binding"], g["right_margin"]
    TM, BM = g["top_margin"], g["bottom_margin"]

    # 2-page spread (odd + even)
    out = build.build_edition(
        f"green-dot-{size}",
        [*content(), *content()],
        "../../src/techo/green_dot/green-dot.tex",
        defs={
            "EDITION": size,
            "BINDING": BINDING,
            "RIGHTMARGIN": RIGHT,
            "DTOP": TM,
            "DBOT": BM,
            "DLEFT": BINDING,
            "DRIGHT": RIGHT,
        },
    )
    print(f"Generated {out}/content.tex + green-dot-{size}.tex ({PW}×{PH}mm, 2 pages)")
    build.write_spread(out, f"green-dot-{size}", PW, PH, booklet=size in ("tn", "tnp"))
    print(f"Generated {out}/spread.pdf (spread, {PW * 2}×{PH}mm)")
