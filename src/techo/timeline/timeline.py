"""Timeline — vertical hour axis on the binding edge, custom start/end hours.

Replicates the mini-tool's timeline (mini-tool/src/tools/timeline.tsx): the
axis hugs the spine, an hour tick + dotted guide line runs into the page,
and a 2-digit label sits in the outer margin.  Hours are spread evenly over
the usable page height; ``--pages 2`` splits the range across the spread.

The left/right (odd/even) typesetting is handled by LaTeX itself: the
template's ``\\timelinepage{start}{end}`` macro draws the axis on the left
margin of odd pages and the right margin of even pages
(``\\ifodd\\value{page}``), so any number of pages lands on the correct
binding side automatically.

Usage: techo timeline [--size a5s] [--start 0] [--end 26] [--pages 1|2] ...

Two steps: ``techo timeline`` generates the per-page edition PDF; run
``techo postprocess timeline-<size> --size <size> --side binding`` to assemble
its print spread.
"""

from .. import build, sizes

MAX_HOUR = 99
DEFAULT_COLOR = "7a7a7a"


def page_range(start: int, end: int, pages: int, swap: bool, is_odd: bool) -> tuple[int, int]:
    """(start, end) hours for one page.

    ``pages=1`` draws the full range on every page; ``pages=2`` splits at the
    midpoint (first half on the even/left page, second half on the odd/right
    page — the spread reads left to right), with ``swap`` exchanging the halves.
    """
    if pages == 1:
        return start, end
    first, second = (start, (start + end) // 2), ((start + end) // 2, end)
    return (first if is_odd else second) if swap else (second if is_odd else first)


def content(start: int, end: int, pages: int = 1, swap: bool = False) -> list[str]:
    """Two-page timeline body: one ``\\timelinepage`` call per page (odd first)."""
    return [
        f"\\timelinepage{{{s}}}{{{e}}}"
        for is_odd in (True, False)
        for s, e in (page_range(start, end, pages, swap, is_odd),)
    ]


def generate(
    size: str,
    *,
    start: int = 0,
    end: int = 26,
    pages: int = 1,
    swap: bool = False,
    color: str = DEFAULT_COLOR,
    compile: bool = True,
) -> None:
    if not 0 <= start < MAX_HOUR:
        raise ValueError(f"start must be in [0, {MAX_HOUR - 1}], got {start}")
    if not start < end <= MAX_HOUR:
        raise ValueError(f"end must satisfy start < end <= {MAX_HOUR}, got {end}")

    s = sizes.SIZES[size]
    g = sizes.green_dot(size)
    PW, PH = s["pw"], s["ph"]
    color = color.lstrip("#").lower()

    out = build.build_edition(
        f"timeline-{size}",
        content(start, end, pages, swap),
        "../../src/techo/timeline/timeline.tex",
        defs={
            "EDITION": size,
            "LABELPT": 10.2,
            "TIMELINECOLOR": color,
            "BINDINGMM": g["binding"],
            "TOPM": g["top_margin"],
            "BOTTOMM": g["bottom_margin"],
        },
        compile=compile,
    )
    label = f"pages={pages}" + (", swapped" if swap else "")
    print(
        f"Generated {out}/content.tex + timeline-{size}.tex "
        f"({PW}×{PH}mm, hours {start:02d}–{end:02d}, {label}); "
        f"pages: {out / f'timeline-{size}.pdf'} — "
        f"post-process with `techo postprocess timeline-{size} --size {size} --side binding`"
    )