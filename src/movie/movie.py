"""Movie / TV rating page — TMDB search, 5-star rating, TV season grids.

Usage: techo movie "<query>" --size 74m5

The title header (localized name, original name, five ☆ stars to fill in by
hand) sits at the top of the first page. TV seasons then flow directly beneath
it as compact midori-style hollow-intersection grids of numbered episode cells,
many seasons per page rather than one page each.
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .. import sizes

TMDB_API = "https://api.themoviedb.org/3"

# midori_grid visual style (see src/midori_grid/midori_grid.py)
PEN = "cyan!40, line width=0.7pt"


# ── Domain types ──


@dataclass(frozen=True)
class Season:
    """One season of a TV show: number, episode count, and TMDB season name."""

    number: int
    episodes: int
    name: str


@dataclass(frozen=True)
class Title:
    """A movie or TV show resolved from TMDB."""

    kind: str  # "movie" | "tv"
    tmdb_id: int
    name: str
    original_name: str
    seasons: tuple[Season, ...] = ()


# ── TMDB client (stdlib urllib; auth read from the environment) ──


def _credentials() -> tuple[str, bool]:
    """Return ``(secret, is_bearer)``.

    Prefers the v4 read access token (``TMDB_ACCESS_TOKEN``) over the v3 api key
    (``TMDB_API_KEY``).
    """
    token = os.environ.get("TMDB_ACCESS_TOKEN")
    if token:
        return token.strip(), True
    key = os.environ.get("TMDB_API_KEY")
    if key:
        return key.strip(), False
    raise RuntimeError(
        "set TMDB_ACCESS_TOKEN (v4) or TMDB_API_KEY (v3) to use the movie command"
    )


def _tmdb_get(path: str, params: dict[str, str], language: str) -> dict:
    """GET a TMDB endpoint and return the parsed JSON, or raise RuntimeError."""
    secret, is_bearer = _credentials()
    query: dict[str, str] = {"language": language, **params}
    if not is_bearer:
        query["api_key"] = secret
    url = f"{TMDB_API}{path}?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(url)
    if is_bearer:
        request.add_header("Authorization", f"Bearer {secret}")
    request.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"TMDB {path} failed ({error.code}): {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"could not reach TMDB: {error.reason}") from error
    try:
        return json.loads(payload)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"TMDB {path} returned non-JSON data") from error


def _year(date_text: str | None) -> str:
    return (date_text or "")[:4]


def _result_summary(result: dict) -> tuple[str, str, str, str]:
    """Return ``(kind, name, original_name, year)`` for a multi-search result."""
    media = result.get("media_type")
    if media == "movie":
        name = result.get("title") or result.get("original_title") or "(untitled)"
        original = result.get("original_title") or ""
        year = _year(result.get("release_date"))
    else:  # tv
        name = result.get("name") or result.get("original_name") or "(untitled)"
        original = result.get("original_name") or ""
        year = _year(result.get("first_air_date"))
    return media or "", name, original, year


def search(query: str, *, language: str, kind: str | None = None) -> list[dict]:
    """Return matching multi-search results (movie/tv only), optionally by kind."""
    payload = _tmdb_get(
        "/search/multi", {"query": query, "include_adult": "false"}, language
    )
    results = payload.get("results", [])
    return [
        r
        for r in results
        if r.get("media_type") in ("movie", "tv")
        and (kind is None or r["media_type"] == kind)
    ]


def fetch_title(kind: str, tmdb_id: int, *, language: str) -> Title:
    """Fetch full details for one movie or TV show."""
    path = f"/{'movie' if kind == 'movie' else 'tv'}/{tmdb_id}"
    data = _tmdb_get(path, {}, language)
    if kind == "movie":
        name = data.get("title") or data.get("original_title") or ""
        original = data.get("original_title") or ""
        seasons: tuple[Season, ...] = ()
    else:
        name = data.get("name") or data.get("original_name") or ""
        original = data.get("original_name") or ""
        seasons = tuple(
            sorted(
                (
                    Season(
                        number=s["season_number"],
                        episodes=s["episode_count"],
                        name=s.get("name") or "",
                    )
                    for s in data.get("seasons", [])
                    if s.get("episode_count", 0) > 0
                ),
                # regular seasons first (1..N), then specials (season 0) last
                key=lambda s: (s.number == 0, s.number),
            )
        )
    return Title(
        kind=kind,
        tmdb_id=tmdb_id,
        name=name,
        original_name=original,
        seasons=seasons,
    )


# ── Pure layout helpers (no I/O; unit-tested) ──


def _tex_escape(text: str | None) -> str:
    """Escape LaTeX special characters."""
    if not text:
        return ""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def _slug(text: str) -> str:
    """Filesystem-safe slug for the output directory (keeps CJK)."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w]+", "-", text, flags=re.UNICODE)
    return text.strip("-") or "untitled"


GRID_CELL = 5.0  # mm — matches midori_grid grid_step


def _cols_that_fit(usable_w: float, cell: float = GRID_CELL) -> int:
    """How many ``cell``-wide columns fit across ``usable_w`` mm (at least one)."""
    return max(1, int(usable_w // cell))


def _cells(
    x0: float, y0: float, count: int, cols: int, cell: float, pen: str = PEN
) -> list[str]:
    """Midori-style outline of exactly ``count`` cells wrapped at ``cols`` columns.

    Each cell is drawn with its four edges; verticals gap at the top, reproducing
    midori_grid's hollow intersections. Overlapping shared edges are drawn twice
    (visually identical), so a ragged last row needs no special handling.
    """
    gap = min(1.5, max(0.5, cell * 0.1))
    lines: list[str] = []
    for i in range(count):
        r = i // cols
        c = i % cols
        xa = x0 + c * cell
        xb = x0 + (c + 1) * cell
        yt = y0 + r * cell
        yb = y0 + (r + 1) * cell
        lines.append(
            f"  \\draw[{pen}]"
            f" ([xshift={xa:.2f}mm, yshift={-yt:.2f}mm]current page.north west)"
            f" -- ([xshift={xb:.2f}mm, yshift={-yt:.2f}mm]current page.north west);"
        )
        lines.append(
            f"  \\draw[{pen}]"
            f" ([xshift={xa:.2f}mm, yshift={-yb:.2f}mm]current page.north west)"
            f" -- ([xshift={xb:.2f}mm, yshift={-yb:.2f}mm]current page.north west);"
        )
        lines.append(
            f"  \\draw[{pen}]"
            f" ([xshift={xa:.2f}mm, yshift={-(yt + gap):.2f}mm]current page.north west)"
            f" -- ([xshift={xa:.2f}mm, yshift={-yb:.2f}mm]current page.north west);"
        )
        lines.append(
            f"  \\draw[{pen}]"
            f" ([xshift={xb:.2f}mm, yshift={-(yt + gap):.2f}mm]current page.north west)"
            f" -- ([xshift={xb:.2f}mm, yshift={-yb:.2f}mm]current page.north west);"
        )
    return lines


def _cell_numbers(
    x0: float, y0: float, cols: int, cell: float, numbers: list[int], font: str
) -> list[str]:
    """Centered number nodes, placed left-to-right, top-to-bottom."""
    nodes: list[str] = []
    for i, num in enumerate(numbers):
        r = i // cols
        c = i % cols
        cx = x0 + (c + 0.5) * cell
        cy = y0 + (r + 0.5) * cell
        nodes.append(
            f"  \\node[font=\\{font}, anchor=center]"
            f" at ([xshift={cx:.2f}mm, yshift={-cy:.2f}mm]current page.north west)"
            f" {{{num}}};"
        )
    return nodes


def _stars(cx: float, y: float, n: int = 5) -> list[str]:
    """A centered row of ``n`` ☆ glyphs at vertical position ``y``."""
    return [
        f"  \\node[font=\\FontMedium, anchor=center]"
        f" at ([xshift={cx:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
        f" {{{{\\starfont {'☆' * n}}}}};"
    ]


# ── Page builders ──


def _margins(size: str) -> tuple[float, float, float, float]:
    """``(binding, right, top, bottom)`` margins, from GREEN_DOT when available."""
    g = sizes.GREEN_DOT.get(
        size,
        {"binding": 12, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    )
    return g["binding"], g["right_margin"], g["top_margin"], g["bottom_margin"]


NAME_DOWN = 6.5  # mm, top → name → next line (FontMedium title)
ORIG_DOWN = 5.0  # mm, original name line height
STAR_PAD = 2.5  # mm, gap above the star row
HEADER_GAP = 4.5  # mm, below the stars before the first season grid


def _rating_header(title: Title, size: str, pw: float) -> tuple[list[str], float]:
    """Name + original name + five ☆ stars as overlay tikz lines.

    Returns ``(lines, height)``, where ``height`` is how far below the page's top
    edge the header reaches — so the season packer can start the first grid right
    beneath it on the same page instead of wasting a page on the header alone.
    """
    binding, right, top, _ = _margins(size)
    usable_w = pw - binding - right
    cx = pw / 2
    lines: list[str] = []
    y = top
    lines.append(
        f"  \\node[font=\\FontMedium, anchor=north, text width={usable_w:.2f}mm,"
        f" align=center]"
        f" at ([xshift={cx:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
        f" {{{_tex_escape(title.name)}}};"
    )
    y += NAME_DOWN
    if (
        title.original_name
        and title.original_name.strip().lower() != (title.name or "").strip().lower()
    ):
        lines.append(
            f"  \\node[font=\\FontSmall, anchor=north, text width={usable_w:.2f}mm,"
            f" align=center]"
            f" at ([xshift={cx:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" {{{_tex_escape(title.original_name)}}};"
        )
        y += ORIG_DOWN
    lines.extend(_stars(cx, y + STAR_PAD))
    return lines, y + STAR_PAD + HEADER_GAP


HDR = 6.0  # mm, season header line
GAP = 4.0  # mm, gap between season blocks


def _season_label(season: Season) -> str:
    """Compact season code: S01, S02, … (S00 for specials)."""
    return f"S{season.number:02d}"


def _pack_seasons(
    seasons: tuple[Season, ...],
    size: str,
    pw: float,
    ph: float,
    *,
    header: list[str] | None = None,
    header_h: float = 0.0,
) -> list[list[str]]:
    """Pack compact per-season grids — exactly one cell per episode, many per page.

    Seasons flow top-to-bottom; each is a header plus a midori-style grid sized to its
    episode count. A season taller than the remaining page space continues on the next
    page (and a season taller than a full page splits its rows across pages).

    When ``header`` is given (the title's name + stars), it is placed at the top of
    the first page and the first season starts ``header_h`` below the top edge, so a
    TV show's rating header shares page 1 with its first season grid instead of
    taking a page to itself. With no seasons, the header still yields one page.
    """
    binding, right, top, bottom = _margins(size)
    usable_w = pw - binding - right
    cell = sizes.MIDORI_GRID.get(size, {}).get("grid_step", GRID_CELL)
    cols = _cols_that_fit(usable_w, cell)
    font = "FontTiny" if cell < 6 else "FontSmall"
    page_top = top
    page_bottom = ph - bottom

    def new_page() -> list[str]:
        return [
            "\\thispagestyle{empty}%",
            "\\begin{tikzpicture}[remember picture, overlay,"
            " every node/.style={inner sep=0pt}]",
        ]

    def close(page: list[str]) -> None:
        page.append("\\end{tikzpicture}%")
        page += ["\\null", "\\clearpage"]

    pages: list[list[str]] = []
    current = new_page()
    if header:
        current += header
        y = page_top + header_h
    else:
        y = page_top
    for season in seasons:
        rows = max(1, math.ceil(season.episodes / cols))
        block_h = HDR + rows * cell
        if block_h <= (page_bottom - page_top) and y + block_h > page_bottom:
            close(current)
            pages.append(current)
            current = new_page()
            y = page_top
        current.append(
            f"  \\node[font=\\FontSmall, anchor=north west]"
            f" at ([xshift={binding:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" {{{_tex_escape(_season_label(season))}}};"
        )
        y += HDR
        placed_rows = 0
        while placed_rows < rows:
            space = page_bottom - y
            if space < cell:
                close(current)
                pages.append(current)
                current = new_page()
                y = page_top
                space = page_bottom - y
            rows_here = min(rows - placed_rows, max(1, int(space // cell)))
            start_ep = placed_rows * cols + 1
            eps_here = min(cols * rows_here, season.episodes - placed_rows * cols)
            current += _cells(binding, y, eps_here, cols, cell)
            current += _cell_numbers(
                binding, y, cols, cell, list(range(start_ep, start_ep + eps_here)), font
            )
            y += rows_here * cell
            placed_rows += rows_here
        y += GAP
    close(current)
    pages.append(current)
    return pages


def _print_matches(results: list[dict]) -> None:
    """Echo a numbered list of search results so the user can pass --index."""
    print(f"Found {len(results)} result(s):")
    for i, result in enumerate(results):
        kind, name, original, year = _result_summary(result)
        extra = []
        if original and original != name:
            extra.append(original)
        if year:
            extra.append(year)
        suffix = f" ({', '.join(extra)})" if extra else ""
        print(f"  [{i}] {kind:<5} {name}{suffix}")


def generate(
    query: str,
    *,
    size: str = "74m5",
    index: int = 0,
    kind: str | None = None,
    language: str = "zh-CN",
    cjk_font: str = "FZBaoSong-Z04S",
    compile: bool = True,
) -> None:
    """Search TMDB and generate the rating page (+ TV season grids)."""
    if size not in sizes.SIZES:
        raise ValueError(f"size '{size}' not found in sizes.py")

    results = search(query, language=language, kind=kind)
    if not results:
        raise ValueError(f"no movie/tv results for {query!r}")
    _print_matches(results)
    if index < 0 or index >= len(results):
        raise ValueError(f"--index {index} out of range (0..{len(results) - 1})")
    chosen = results[index]

    title = fetch_title(chosen["media_type"], chosen["id"], language=language)

    sizes.write_sizes_tex()
    dims = sizes.SIZES[size]
    pw, ph = dims["pw"], dims["ph"]

    slug = _slug(title.name or query)
    out = Path("outputs") / f"movie-{slug}-{size}"
    out.mkdir(parents=True, exist_ok=True)

    header_lines, header_h = _rating_header(title, size, pw)
    pages = _pack_seasons(
        title.seasons, size, pw, ph, header=header_lines, header_h=header_h
    )
    (out / "content.tex").write_text("\n".join("\n".join(p) for p in pages) + "\n")

    tex_name = f"movie-{slug}-{size}.tex"
    (out / tex_name).write_text(
        f"\\def\\EDITION{{{size}}}%\n"
        f"\\def\\CJKFONT{{{cjk_font}}}%\n"
        f"\\input{{../../src/movie/movie.tex}}%\n"
    )

    print(
        f"Generated {out}/content.tex + {tex_name} "
        f"({title.kind}: {title.name}, {len(pages)} page(s), {pw}×{ph}mm)"
    )

    if compile:
        sizes.compile(tex_name, out)
        print(f"Compiled {out}/{tex_name.removesuffix('.tex')}.pdf")
