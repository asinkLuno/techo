"""Ruled — a page of evenly spaced horizontal writing lines.

Usage: techo ruled --size a5s [--gap 5.0] [--top 10.0] [--bottom 10.0]
       [--left 15.0] [--right 5.0] [--color 7a7a7a]
"""

from .. import build, sizes
from ..texutil import tex_escape


def content() -> list[str]:
    """Return LaTeX lines for a single empty ruled page."""
    return [
        "\\thispagestyle{empty}%",
        "\\null",
        "\\clearpage",
    ]


def generate(
    size: str,
    *,
    gap: float = 5.0,
    top: float = 10.0,
    bottom: float = 10.0,
    left: float = 15.0,
    right: float = 5.0,
    color: str = "7a7a7a",
    compile: bool = True,
) -> None:
    """Generate a 2-page ruled spread for *size*."""
    s = sizes.SIZES[size]
    PW, PH = s["pw"], s["ph"]
    color = color.lstrip("#").lower()

    out = build.build_edition(
        f"ruled-{size}",
        [*content(), *content()],
        "../../src/techo/ruled/ruled.tex",
        defs={
            "EDITION": size,
            "RULEDGAP": gap,
            "RULEDTOP": top,
            "RULEDBOT": bottom,
            "RULEDLEFT": left,
            "RULEDRIGHT": right,
            "RULEDCOLOR": color,
        },
        compile=compile,
    )
    print(
        f"Generated {out}/content.tex + ruled-{size}.tex "
        f"({PW}×{PH}mm, gap {gap}mm, margins top/bottom/left/right "
        f"{top}/{bottom}/{left}/{right}mm)"
    )