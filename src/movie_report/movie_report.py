"""Movie / TV "Archival Dossier" — a fillable viewing report (TMDB + LaTeX).

Usage: techo movie-report "<query>" --size a5

Recreates the Stitch *Retro Cinema Lab Report — 观影报告 布局优化版 (Annotated
Fix)* as a printable, fillable report. TMDB fills in the title's identity — the
localized name (and original name) as TITLE, the release/air date as a red DATE
stamp, and (for TV) one checkable stamp per episode grouped into SEASON cards so
the viewer can mark each as completed. Everything else — the episode stamps
themselves, the internal field-notes box — is left blank for the user to fill by
hand. A pseudo "dossier code" derived from the title flavours the progress-log
header and the footer ref code.

The page itself is the pale-olive "dossier sheet"; a dashed poster slot, white
season cards with a hard offset shadow, a red rotated date stamp, a perforated
tear line, and a FILE_ACTIVE stamp sit on top of it.
"""

from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .. import sizes
from ..movie.movie import (
    Season,
    _print_matches,
    _resolve_cjk_font,
    _slug,
    _tex_escape,
    _tmdb_get,
    search,
)

_MONTHS = (
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
)

# A movie gets this many blank stamps in its SCREENING card (a rewatch tally).
_MOVIE_STAMPS = 8


# ── Domain type ──


@dataclass(frozen=True)
class Report:
    """A movie or TV show resolved from TMDB, with the fields the report prints."""

    kind: str  # "movie" | "tv"
    name: str
    original_name: str
    date: str  # ISO YYYY-MM-DD (release_date / first_air_date)
    seasons: tuple[Season, ...]
    poster_path: str = ""  # TMDB poster_path, e.g. "/abc.jpg"


# ── TMDB fetch (reuses movie's stdlib client) ──


def fetch_report(kind: str, tmdb_id: int, *, language: str) -> Report:
    """Fetch the report fields for one movie or TV show."""
    path = f"/{'movie' if kind == 'movie' else 'tv'}/{tmdb_id}"
    data = _tmdb_get(path, {}, language)
    if kind == "movie":
        name = data.get("title") or data.get("original_title") or ""
        original = data.get("original_title") or ""
        date = data.get("release_date") or ""
        seasons: tuple[Season, ...] = ()
    else:
        name = data.get("name") or data.get("original_name") or ""
        original = data.get("original_name") or ""
        date = data.get("first_air_date") or ""
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
    return Report(
        kind=kind,
        name=name,
        original_name=original,
        date=date,
        seasons=seasons,
        poster_path=data.get("poster_path") or "",
    )


# ── Poster download (TMDB image CDN needs no auth) ──

TMDB_IMG = "https://image.tmdb.org/t/p/w500"


def _download_poster(poster_path: str, dest: Path) -> bool:
    """Download the w500 poster to ``dest``; return False (and warn) on failure."""
    request = urllib.request.Request(
        TMDB_IMG + poster_path, headers={"Accept": "image/*"}
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            dest.write_bytes(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as error:
        print(f"warning: poster download failed ({error}); using placeholder")
        return False
    return True


# ── Pure formatting helpers (no I/O; unit-tested) ──


def _format_date(iso: str | None) -> str:
    """``2010-07-15`` → ``JUL-15-2010`` (the report's MON-DD-YYYY stamp).

    Unparseable or missing input is returned unchanged (empty if falsy), so a
    bad date never breaks the build.
    """
    if not iso:
        return ""
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso)
    if not match:
        return iso
    year, month, day = match.groups()
    month_index = int(month)
    if not 1 <= month_index <= 12:
        return iso
    return f"{_MONTHS[month_index - 1]}-{int(day):02d}-{year}"


def _initials(text: str | None) -> str:
    """Initials of the ASCII words in ``text``: ``"Breaking Bad"`` → ``"BB"``.

    Falls back to ``"XX"`` so the dossier code is never empty (e.g. CJK-only
    titles with no romanized words).
    """
    tokens = re.findall(r"[A-Za-z0-9]+", text or "")
    code = "".join(token[0] for token in tokens)[:4].upper()
    return code or "XX"


def _dossier_code(report: Report) -> str:
    """Short code for the progress-log header, e.g. ``DOSSIER_BB_01``."""
    return _initials(report.original_name or report.name)


def _ref_code(report: Report) -> str:
    """Footer ref code: ``{INITIALS}-{YEAR}``, e.g. ``BB-2008``."""
    year = report.date[:4] if report.date else "0000"
    return f"{_dossier_code(report)}-{year}"


def _stamp_cols(pw_mm: float) -> int:
    """How many EP stamps fit per card row (clamped 4..10)."""
    usable = pw_mm - 20.0  # 10 mm geometry margin each side
    return max(4, min(10, int(usable // 18.0)))


# ── LaTeX section builders (pure; return LaTeX source) ──


def _title_section(report: Report, poster_file: str | None = None) -> str:
    """Poster slot, then TITLE (left, underlined) | DATE (right, red stamp).

    ``poster_file`` (a filename in the output dir) shows the fetched TMDB
    poster; without it the dashed "ATTACH POSTER HERE" placeholder is printed.
    """
    poster = (
        rf"\posterimage{{{_tex_escape(poster_file)}}}" if poster_file else r"\posterbox"
    )
    lines = [
        r"\noindent\begin{center}",
        poster,
        r"\end{center}",
        r"\vspace{8pt}",
        r"\noindent\begin{minipage}[b]{0.57\linewidth}",
        r"\caplabel{TITLE}\\[3pt]",
        rf"{{\fontsize{{16pt}}{{18pt}}\selectfont\displfont\bfseries"
        rf" \MakeUppercase{{{_tex_escape(report.name)}}}}}",
    ]
    if (
        report.original_name
        and report.original_name.strip().lower() != report.name.strip().lower()
    ):
        lines.append(
            rf"\\[2pt]{{\fontsize{{8pt}}{{9pt}}\selectfont\itshape"
            rf" {_tex_escape(report.original_name)}}}"
        )
    lines.append(r"\\[3pt]{\color{Outline}\rule{\linewidth}{0.8pt}}")
    lines.append(r"\end{minipage}\hfill")
    lines.append(r"\begin{minipage}[b]{0.40\linewidth}\raggedleft")
    lines.append(r"\caplabel{DATE}\\[6pt]")
    lines.append(rf"\datestamp{{{_tex_escape(_format_date(report.date))}}}")
    lines.append(r"\end{minipage}")
    lines.append(r"\par")
    return "\n".join(lines)


def _progress_header(report: Report) -> str:
    """Section rule: ``PROGRESS LOG: DOSSIER_xx_01`` … ``STAMP EPISODES AS COMPLETED``."""
    code = _dossier_code(report)
    label = _tex_escape(f"PROGRESS LOG: DOSSIER_{code}_01")
    right = (
        "STAMP EPISODES AS COMPLETED" if report.kind == "tv" else "MARK AS COMPLETED"
    )
    return "\n".join(
        [
            rf"\noindent\caplabel{{{label}}}"
            rf"\hfill\caplabel{{{right}}}\par",
            r"\vspace{1pt}{\color{Outline}\hrule height 0.5pt}\vspace{6pt}",
        ]
    )


def _spread_grid(items: list[str], cols: int) -> str:
    """Lay ``items`` (already-formatted LaTeX) ``cols`` per row, spread with \hfill."""
    if not items:
        return ""
    rows = []
    for start in range(0, len(items), cols):
        chunk = items[start : start + cols]
        rows.append(r"\noindent" + r"\hfill".join(chunk) + r"\par")
    return "\n".join(rows)


def _season_cards(report: Report, cols: int) -> str:
    """One dossier card per TV season, each with a grid of ``EP NN`` stamps."""
    lines: list[str] = []
    for season in report.seasons:
        items = [rf"\epitem{{{n:02d}}}" for n in range(1, season.episodes + 1)]
        grid = _spread_grid(items, cols)
        lines.append(rf"\dossiercard{{SEASON {season.number:02d}}}{{{grid}}}")
        lines.append(r"\vspace{7pt}")
    return "\n".join(lines)


def _screening_card(report: Report, cols: int) -> str:
    """A single dossier card for a movie — a row of blank rewatch stamps."""
    items = [rf"\stamp{{{n}}}" for n in range(1, _MOVIE_STAMPS + 1)]
    grid = _spread_grid(items, cols)
    return rf"\dossiercard{{SCREENING}}{{{grid}}}"


def _progress_cards(report: Report, cols: int) -> str:
    """Season cards for TV, or one screening card for a movie."""
    if report.kind == "tv" and report.seasons:
        return _season_cards(report, cols)
    return _screening_card(report, cols)


def _body(report: Report, cols: int, poster_file: str | None = None) -> str:
    """Assemble the full document body — everything on the dossier sheet."""
    return "\n".join(
        [
            _title_section(report, poster_file),
            r"\vspace{10pt}",
            "",
            _progress_header(report),
            _progress_cards(report, cols),
            r"\vspace{2pt}",
            r"\perf",
            r"\notesbox",
            rf"\reportfooter{{{_tex_escape(_ref_code(report))}}}",
        ]
    )


# ── Entry point ──


def generate(
    query: str,
    *,
    size: str = "a5",
    index: int = 0,
    kind: str | None = None,
    language: str = "zh-CN",
    cjk_font: str = "src/索尼明体.ttf",
    compile: bool = True,
) -> None:
    """Search TMDB and generate the fillable viewing report."""
    if size not in sizes.SIZES:
        raise ValueError(f"size '{size}' not found in sizes.py")

    results = search(query, language=language, kind=kind)
    if not results:
        raise ValueError(f"no movie/tv results for {query!r}")
    _print_matches(results)
    if index < 0 or index >= len(results):
        raise ValueError(f"--index {index} out of range (0..{len(results) - 1})")
    chosen = results[index]

    report = fetch_report(chosen["media_type"], chosen["id"], language=language)

    sizes.write_sizes_tex()
    dims = sizes.SIZES[size]
    pw, ph = dims["pw"], dims["ph"]
    cols = _stamp_cols(pw)

    slug = _slug(report.name or query)
    out = Path("outputs") / f"movie-report-{slug}-{size}"
    out.mkdir(parents=True, exist_ok=True)

    # Fetch the TMDB poster into the output dir; fall back to the placeholder.
    poster_file: str | None = None
    if report.poster_path:
        ext = os.path.splitext(report.poster_path)[1] or ".jpg"
        dest = out / f"poster{ext}"
        if _download_poster(report.poster_path, dest):
            poster_file = dest.name

    (out / "content.tex").write_text(_body(report, cols, poster_file) + "\n")

    tex_name = f"movie-report-{slug}-{size}.tex"
    font_name, font_path = _resolve_cjk_font(cjk_font, out)
    wrapper = [f"\\def\\EDITION{{{size}}}%\n", f"\\def\\CJKFONT{{{font_name}}}%\n"]
    if font_path is not None:
        wrapper.append(f"\\def\\CJKFONTPATH{{{font_path}/}}%\n")
    wrapper.append("\\input{../../src/movie_report/movie_report.tex}%\n")
    (out / tex_name).write_text("".join(wrapper))

    n_seasons = len(report.seasons)
    detail = f"{report.kind}" + (f", {n_seasons} season(s)" if n_seasons else "")
    print(
        f"Generated {out}/content.tex + {tex_name} "
        f"({detail}: {report.name}, {pw}x{ph}mm)"
    )

    if compile:
        sizes.compile(tex_name, out)
        print(f"Compiled {out}/{tex_name.removesuffix('.tex')}.pdf")
