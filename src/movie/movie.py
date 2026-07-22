"""Movie / TV rating page — TMDB search, 5-star rating, TV season grids.

Usage: techo movie "<query>" --size 74m5

The whole page is a continuous midori grid (the same one ``midori-grid`` prints),
used as a full-page background. Onto it we "print" content one glyph per cell, like
stamping text onto a ready-made grid notebook: the title (localized name, original
name, five ☆ rating stars) across the top rows, then each TV season as a ``S01``
label followed by its episode numbers 1..N flowing cell by cell.
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
from ..midori_grid.midori_grid import grid_lines as _midori_grid_lines

TMDB_API = "https://api.themoviedb.org/3"


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


def _cols_that_fit(usable_w: float, cell: float) -> int:
    """How many ``cell``-wide columns fit across ``usable_w`` mm (at least one)."""
    return max(1, int(usable_w // cell))


# Midori grid fallback (matches sizes.MIDORI_GRID for the common 5mm sizes).
_MIDORI_DEFAULTS = {
    "binding": 12,
    "right_margin": 5,
    "top_margin": 5,
    "bottom_margin": 5,
    "grid_step": 5.0,
    "dot_freq": 10,
    "gap_size": 1.0,
    "edge_extension": 1.2,
}


@dataclass(frozen=True)
class Geometry:
    """Centered midori-grid geometry shared by the background and the printed cells."""

    start_x: float
    start_y: float
    num_x: int
    num_y: int
    step: float
    gap: float
    ext: float
    dot_freq: int


def _grid_geometry(size: str, pw: float, ph: float) -> Geometry:
    """Centered midori grid for ``size`` — the full-page background the page prints on.

    Both the background grid and every printed glyph are derived from this, so a
    character at column ``c``, row ``r`` always sits in the cell whose outline the
    background draws.
    """
    g = sizes.MIDORI_GRID.get(size, _MIDORI_DEFAULTS)
    binding = g["binding"]
    right = g["right_margin"]
    top = g["top_margin"]
    bottom = g["bottom_margin"]
    step = g["grid_step"]
    usable_w = pw - binding - right
    usable_h = ph - top - bottom
    num_x = _cols_that_fit(usable_w, step)
    num_y = _cols_that_fit(usable_h, step)
    grid_w = num_x * step
    grid_h = num_y * step
    start_x = binding + (usable_w - grid_w) / 2.0
    start_y = top + (usable_h - grid_h) / 2.0
    return Geometry(
        start_x,
        start_y,
        num_x,
        num_y,
        step,
        g["gap_size"],
        g["edge_extension"],
        int(g["dot_freq"]),
    )


def _coord_page(x: float, y: float) -> str:
    """TikZ point anchored to the page corner — matches the content nodes."""
    return f"([xshift={x:.2f}mm, yshift={-y:.2f}mm]current page.north west)"


def _grid_background(geo: Geometry) -> list[str]:
    """The full-page midori grid, page-corner-anchored so it underlays the cells."""
    return _midori_grid_lines(
        geo.start_x,
        geo.start_y,
        geo.num_x,
        geo.num_y,
        step=geo.step,
        gap=geo.gap,
        ext=geo.ext,
        dot_freq=geo.dot_freq,
        coord=_coord_page,
    )


def _cell_node(geo: Geometry, row: int, col: int, content: str, font: str) -> str:
    """One glyph centered in cell ``(row, col)`` of the background grid."""
    cx = geo.start_x + (col + 0.5) * geo.step
    cy = geo.start_y + (row + 0.5) * geo.step
    return (
        f"  \\node[font=\\{font}, anchor=center]"
        f" at ([xshift={cx:.2f}mm, yshift={-cy:.2f}mm]current page.north west)"
        f" {{{content}}};"
    )


def _print_text(
    geo: Geometry, start_row: int, text: str | None, font: str
) -> tuple[list[str], int]:
    """Print ``text`` one character per cell from ``(start_row, 0)``.

    Whitespace occupies a cell but prints nothing (a blank cell). Wraps at
    ``num_x`` columns. Returns ``(nodes, rows_consumed)``.
    """
    chars = list(text or "")
    if not chars:
        return [], 0
    nodes: list[str] = []
    for i, ch in enumerate(chars):
        if ch.isspace():
            continue
        col = i % geo.num_x
        row = start_row + i // geo.num_x
        nodes.append(_cell_node(geo, row, col, _tex_escape(ch), font))
    return nodes, math.ceil(len(chars) / geo.num_x)


def _print_numbers(
    geo: Geometry, start_row: int, numbers: list[int], font: str
) -> tuple[list[str], int]:
    """Print ``numbers`` one per cell, wrapping at ``num_x``. Returns ``(nodes, rows)``."""
    if not numbers:
        return [], 0
    nodes = [
        _cell_node(geo, start_row + i // geo.num_x, i % geo.num_x, str(n), font)
        for i, n in enumerate(numbers)
    ]
    return nodes, math.ceil(len(numbers) / geo.num_x)


def _stars_row(geo: Geometry, row: int, n: int = 5) -> list[str]:
    """A row of ``n`` ☆ glyphs, one per cell, starting at column 0."""
    return [_cell_node(geo, row, i, r"\starfont ☆", "FontMedium") for i in range(n)]


# ── Page builders ──

# Fonts: the title leads at FontMedium; everything else steps down. Episode numbers
# are tiny because a 5mm cell is small, matching the old per-cell numbering.
NAME_FONT = "FontMedium"
LINE_FONT = "FontSmall"
NUM_FONT = "FontTiny"


def _rating_font(geo: Geometry) -> str:
    """Episode-number font: Tiny for small cells, Small once they're roomy."""
    return NUM_FONT if geo.step < 6 else LINE_FONT


HEADER_GAP_ROWS = 1  # blank grid rows between the rating header and the first season


def _header_lines(title: Title, geo: Geometry) -> tuple[list[str], int]:
    """Name + original name + five ☆ stars printed one glyph per cell.

    Returns ``(nodes, rows_consumed)`` measured from grid row 0, including the
    trailing blank gap rows so the season packer can start right beneath.
    """
    nodes: list[str] = []
    row = 0
    added, n = _print_text(geo, row, title.name, NAME_FONT)
    nodes += added
    row += max(n, 1)
    if (
        title.original_name
        and title.original_name.strip().lower() != (title.name or "").strip().lower()
    ):
        added, n = _print_text(geo, row, title.original_name, LINE_FONT)
        nodes += added
        row += max(n, 1)
    nodes += _stars_row(geo, row)
    row += 1
    row += HEADER_GAP_ROWS
    return nodes, row


HDR_FONT = LINE_FONT


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
    header_rows: int = 0,
) -> list[list[str]]:
    """Pack seasons onto full-page midori grids — one cell per episode, many per page.

    Every page begins with the continuous background grid; content is printed on top
    in grid-row units. The rating ``header`` (if given) sits at the top of page 1 and
    the first season starts ``header_rows`` down, so a TV show's header shares page 1
    with its first season. Seasons flow top-to-bottom; a season taller than the
    remaining page space continues on the next page (and one taller than a full page
    splits its rows across pages). With no seasons, the header still yields one page.
    """
    geo = _grid_geometry(size, pw, ph)
    cols = geo.num_x
    page_rows = geo.num_y
    num_font = _rating_font(geo)

    def new_page() -> list[str]:
        return [
            "\\thispagestyle{empty}%",
            "\\begin{tikzpicture}[remember picture, overlay,"
            " every node/.style={inner sep=0pt}]",
            *_grid_background(geo),
        ]

    def close(page: list[str]) -> None:
        page.append("\\end{tikzpicture}%")
        page += ["\\null", "\\clearpage"]

    pages: list[list[str]] = []
    current = new_page()
    if header:
        current += header
        row = header_rows
    else:
        row = 0
    for season in seasons:
        episodes = season.episodes
        ep_rows = max(1, math.ceil(episodes / cols))
        block_rows = 1 + ep_rows  # label row + episode rows
        # Move the whole block to a new page if it won't fit and we're not at the top.
        if row + block_rows > page_rows and row > 0:
            close(current)
            pages.append(current)
            current = new_page()
            row = 0
        label_nodes, _ = _print_text(geo, row, _season_label(season), HDR_FONT)
        current += label_nodes
        row += 1
        placed = 0
        while placed < episodes:
            if row >= page_rows:
                close(current)
                pages.append(current)
                current = new_page()
                row = 0
            space_rows = page_rows - row
            remaining = episodes - placed
            rows_here = min(math.ceil(remaining / cols), space_rows)
            eps_here = min(rows_here * cols, remaining)
            nodes, _ = _print_numbers(
                geo, row, list(range(placed + 1, placed + 1 + eps_here)), num_font
            )
            current += nodes
            row += rows_here
            placed += eps_here
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

    geo = _grid_geometry(size, pw, ph)
    header_lines, header_rows = _header_lines(title, geo)
    pages = _pack_seasons(
        title.seasons, size, pw, ph, header=header_lines, header_rows=header_rows
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
