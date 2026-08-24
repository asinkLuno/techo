"""Plain ruled notebook generator — CLI entry point.

All builds go through the `techo` command:
  techo nightowl --size m5|cozyca|74m5
  techo senary YYYY-MM [--base tranquillity] [--partner cnsa]
  techo movie "<query>" --size 74m5 [--type movie|tv] [--index N]
"""

from pathlib import Path

import click

from . import sizes
from .ebook import ebook
from .green_dot import generate as gen_green_dot
from .midori_grid.midori_grid import generate as gen_midori_grid
from .movie_report.movie_report import generate as gen_movie_report
from .nightowl import generate as gen_nightowl
from .senary import generate as gen_senary
from .senary.bases import BASES
from .senary.partners import PARTNERS
from .timeline.timeline import generate as gen_timeline
from .timeline.timeline import merge as gen_timeline_merge
from .tn_cover import generate as gen_tn_cover


@click.group()
def cli() -> None:
    """Generate printable notebooks, covers, and books."""


def _run(generator, /, *args, **kwargs) -> None:
    """Present domain and operating-system failures consistently in Click."""
    try:
        generator(*args, **kwargs)
    except (OSError, RuntimeError, ValueError) as error:
        raise click.ClickException(str(error)) from error


cli.add_command(ebook)


@cli.command("nightowl")
@click.option(
    "--size",
    default="67m5",
    show_default=True,
    type=click.Choice(list(sizes.NIGHTOWL.keys())),
)
def nightowl(size: str) -> None:
    """Triangular numbers 0–26 in hourglass layout."""
    _run(gen_nightowl, size)


@cli.command("senary")
@click.argument("ym")
@click.option(
    "--base",
    "base_id",
    default="tranquillity",
    show_default=True,
    type=click.Choice(list(BASES.keys())),
    help="Lunar base the almanac is computed for.",
)
@click.option(
    "--partner",
    "partner_id",
    default="cnsa",
    show_default=True,
    type=click.Choice(list(PARTNERS.keys())),
    help="Earth partner (relay organisation) for the time axis.",
)
def senary(ym: str, base_id: str, partner_id: str) -> None:
    """Lunar-almanac month book: calendar + tracker + day pages. YYYY-MM."""
    _run(gen_senary, ym, base_id=base_id, partner_id=partner_id)


@cli.command("green-dot")
@click.option(
    "--size",
    default="67m5",
    show_default=True,
    type=click.Choice(list(sizes.SIZES.keys())),
)
def green_dot(size: str) -> None:
    """Single empty page with green-dot grid background."""
    _run(gen_green_dot, size)


@cli.command("midori-grid")
@click.option(
    "--size",
    default="a5s",
    show_default=True,
    type=click.Choice(list(sizes.MIDORI_GRID.keys())),
)
def midori_grid(size: str) -> None:
    """Midori Grid — square grids with hollow intersections."""
    _run(gen_midori_grid, size)


@cli.command("timeline")
@click.option(
    "--size",
    default="a5s",
    show_default=True,
    type=click.Choice(list(sizes.SIZES.keys())),
)
@click.option("--start", default=0, show_default=True, type=click.IntRange(0, 98), help="Start hour.")
@click.option("--end", default=26, show_default=True, type=click.IntRange(1, 99), help="End hour (must be > start).")
@click.option(
    "--pages",
    default=1,
    show_default=True,
    type=click.Choice(["1", "2"]),
    help="1: full range on every page; 2: split across the spread.",
)
@click.option("--swap", is_flag=True, help="Swap which half of the range each page gets (with --pages 2).")
@click.option("--color", default="7a7a7a", show_default=True, help="Ticks/labels color as hex (e.g. 7a7a7a).")
def timeline(size: str, start: int, end: int, pages: str, swap: bool, color: str) -> None:
    """Hour axis on the binding edge with custom start/end hours."""
    _run(gen_timeline, size, start=start, end=end, pages=int(pages), swap=swap, color=color)


@cli.command("timeline-merge")
@click.option(
    "--size",
    default="a5s",
    show_default=True,
    type=click.Choice(list(sizes.SIZES.keys())),
)
@click.option(
    "--side",
    default="binding",
    show_default=True,
    type=click.Choice(["binding", "outer"]),
    help="binding: axes hug the spine, numbers toward the binding; outer: axes at the outer edges.",
)
def timeline_merge(size: str, side: str) -> None:
    """Assemble the merged print spread from generated timeline pages."""
    _run(gen_timeline_merge, size, side=side)


@cli.command("movie-report")
@click.argument("query")
@click.option(
    "--size",
    default="a5",
    show_default=True,
    type=click.Choice(list(sizes.SIZES.keys())),
)
@click.option(
    "--index", default=0, show_default=True, help="Pick the Nth search result."
)
@click.option(
    "--type",
    "kind",
    default=None,
    type=click.Choice(["movie", "tv"]),
    help="Restrict the search to movies or TV shows.",
)
@click.option("--language", default="zh-CN", show_default=True)
@click.option("--cjk-font", default="src/索尼明体.ttf", show_default=True)
@click.option("--no-compile", is_flag=True, help="Write LaTeX only, skip xelatex.")
def movie_report(
    query: str,
    size: str,
    index: int,
    kind: str,
    language: str,
    cjk_font: str,
    no_compile: bool,
) -> None:
    """Movie/TV archival "lab report" — a fillable viewing dossier (TMDB)."""
    _run(
        gen_movie_report,
        query,
        size=size,
        index=index,
        kind=kind,
        language=language,
        cjk_font=cjk_font,
        compile=not no_compile,
    )


@cli.command("tn-cover")
@click.argument(
    "image-path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--size",
    default="tn",
    show_default=True,
    type=click.Choice(["tn", "tnp"]),
)
def tn_cover(image_path: Path, size: str) -> None:
    """Generate Traveler's Notebook (TN/TNP) cover spread from an image."""
    _run(gen_tn_cover, image_path, size)


if __name__ == "__main__":
    cli()
