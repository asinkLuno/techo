"""Plain ruled notebook generator — CLI entry point.

All builds go through the `techo` command:
  techo nightowl --size m5|cozyca|74m5
  techo senary YYYY-MM [--tz Asia/Shanghai] [--location tranquility]
"""

from pathlib import Path

import click

from . import sizes
from .green_dot import generate as gen_green_dot
from .midori_grid.midori_grid import generate as gen_midori_grid
from .nightowl import generate as gen_nightowl
from .senary import LOCATIONS
from .senary import generate as gen_senary
from .tn_cover import generate as gen_tn_cover


@click.group()
def cli() -> None:
    pass


@cli.command("nightowl")
@click.option(
    "--size",
    default="67m5",
    show_default=True,
    type=click.Choice(list(sizes.NIGHTOWL.keys())),
)
def nightowl(size: str) -> None:
    """Triangular numbers 0–26 in hourglass layout."""
    gen_nightowl(size)


@cli.command("senary")
@click.argument("ym")
@click.option(
    "--tz", default="UTC", show_default=True, help="IANA name, e.g. Asia/Shanghai"
)
@click.option(
    "--location",
    default="tranquility",
    show_default=True,
    type=click.Choice(list(LOCATIONS.keys())),
)
def senary(ym: str, tz: str, location: str) -> None:
    """Monthly calendar (front) + habit tracker (back). YYYY-MM, e.g. 2026-07."""
    gen_senary(ym, tz_name=tz, location=location)


@cli.command("green-dot")
@click.option(
    "--size",
    default="67m5",
    show_default=True,
    type=click.Choice(list(sizes.SIZES.keys())),
)
def green_dot(size: str) -> None:
    """Single empty page with green-dot grid background."""
    gen_green_dot(size)


@cli.command("midori-grid")
@click.option(
    "--size",
    default="a5s",
    show_default=True,
    type=click.Choice(list(sizes.MIDORI_GRID.keys())),
)
def midori_grid(size: str) -> None:
    """Midori Grid — square grids with hollow intersections."""
    gen_midori_grid(size)


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
    gen_tn_cover(image_path, size)


if __name__ == "__main__":
    cli()
