"""Plain ruled notebook generator — CLI entry point."""

import click

import nightowl
import senary
import sizes
import xianzhang


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option(
    "--size",
    default="m5",
    show_default=True,
    type=click.Choice(list(sizes.NIGHTOWL.keys())),
)
def nightowl_cmd(size: str) -> None:
    """Triangular numbers 0–26 in hourglass layout."""
    nightowl.generate(size)


@cli.command()
@click.argument("edition", type=click.Choice(list(sizes.XIANZHANG.keys())))
def xianzhang_cmd(edition: str) -> None:
    """French ruled (Séyès) notebook."""
    xianzhang.generate(f"xianzhang-{edition}")


@cli.command("senary")
@click.argument("ym")
def senary_cmd(ym: str) -> None:
    """Monthly calendar (front) + habit tracker (back). YYYY-MM, e.g. 2026-07."""
    senary.generate(ym)
