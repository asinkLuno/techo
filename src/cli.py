"""Plain ruled notebook generator — CLI entry point.

All builds go through the `techo` command:
  techo nightowl --size m5|cozyca|74m5
  techo senary YYYY-MM [--tz Asia/Shanghai] [--location tranquility]
  techo linear --size a5s
"""

import click

import sizes
from linear import generate as gen_linear
from nightowl import generate as gen_nightowl
from senary import LOCATIONS
from senary import generate as gen_senary
from seyes import generate as gen_seyes


@click.group()
def cli() -> None:
    pass


@cli.command("nightowl")
@click.option(
    "--size",
    default="m5",
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


@cli.command("linear")
@click.option(
    "--size",
    default="a5s",
    show_default=True,
    type=click.Choice(list(sizes.LINEAR.keys())),
)
def linear(size: str) -> None:
    """Ruled pages — 7mm spaced horizontal lines, 2mm thick."""
    gen_linear(size)


@cli.command("seyes")
@click.option(
    "--size",
    default="tn",
    show_default=True,
    type=click.Choice(list(sizes.SEYES.keys())),
)
@click.option(
    "--sheets",
    default=1,
    show_default=True,
    help="Number of physical sheets (1 sheet = 4 pages)",
)
def seyes(size: str, sheets: int) -> None:
    """French-ruled pages (Seyes) — blue lines every 2mm, red vertical margin."""
    gen_seyes(size, sheets=sheets)


if __name__ == "__main__":
    cli()
