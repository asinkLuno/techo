"""Plain ruled notebook generator — CLI entry point.

All builds go through the `techo` command:
  techo nightowl --size m5|cozyca|74m5
  techo xianzhang <cozyca|m5|74m5|a5s>
  techo senary YYYY-MM [--tz Asia/Shanghai] [--location tranquility]
  techo day YYYY-MM-DD [--tz Asia/Shanghai] [--location tranquility]
"""

import click

import sizes
from nightowl import generate as gen_nightowl
from senary import LOCATIONS
from senary import generate as gen_senary
from senary.day import generate as gen_day
from xianzhang import generate as gen_xianzhang


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


@cli.command("xianzhang")
@click.argument("edition", type=click.Choice(list(sizes.XIANZHANG.keys())))
def xianzhang(edition: str) -> None:
    """French ruled (Séyès) notebook."""
    gen_xianzhang(f"xianzhang-{edition}")


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


@cli.command("day")
@click.argument("ymd")
@click.option(
    "--tz", default="UTC", show_default=True, help="IANA name, e.g. Asia/Shanghai"
)
@click.option(
    "--location",
    default="tranquility",
    show_default=True,
    type=click.Choice(list(LOCATIONS.keys())),
)
def day(ymd: str, tz: str, location: str) -> None:
    """Single day timeline. YYYY-MM-DD, e.g. 2026-07-15."""
    gen_day(ymd, tz_name=tz, location=location)


if __name__ == "__main__":
    cli()
