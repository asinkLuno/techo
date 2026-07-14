"""Commands for preparing EPUB and Markdown books for print."""

from pathlib import Path

import click

from .. import sizes
from .extract import epub_to_markdown
from .render import render_book
from .split import split_omnibus


@click.group()
def ebook() -> None:
    """Extract, split, or typeset electronic books."""


@ebook.command("extract")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument("output_dir", required=False, type=click.Path(path_type=Path))
@click.option("--flat", is_flag=True, help="Do not create chapter directories.")
def extract(input_path: Path, output_dir: Path | None, flat: bool) -> None:
    """Extract an EPUB into Markdown files following its table of contents."""
    destination = output_dir or input_path.with_suffix("")
    written = epub_to_markdown(input_path, destination, flat=flat)
    click.echo(f"Wrote {len(written)} sections to {destination}")


@ebook.command("split")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument("output_dir", required=False, type=click.Path(path_type=Path))
def split(input_path: Path, output_dir: Path | None) -> None:
    """Split an omnibus EPUB using top-level TOC sections."""
    destination = output_dir or input_path.with_name(f"{input_path.stem}-split")
    written = split_omnibus(input_path, destination)
    click.echo(f"Wrote {len(written)} books to {destination}")


@ebook.command("render")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument("output_path", required=False, type=click.Path(path_type=Path))
@click.option(
    "--size", default="a5s", show_default=True, type=click.Choice(list(sizes.SIZES))
)
@click.option("--font", default="FZBaoSong-Z04S", show_default=True)
@click.option("--sans-font", default="AR PL UMing CN", show_default=True)
@click.option("--mono-font", default="AR PL UMing CN", show_default=True)
@click.option("--font-size", default="8pt", show_default=True)
@click.option("--indent", default=None, metavar="DIMENSION")
@click.option(
    "--one-sided", is_flag=True, help="Use symmetric margins and centered page numbers."
)
@click.option("--tex", is_flag=True, help="Write LaTeX instead of compiling a PDF.")
def render(
    input_path: Path,
    output_path: Path | None,
    size: str,
    font: str,
    sans_font: str,
    mono_font: str,
    font_size: str,
    indent: str | None,
    one_sided: bool,
    tex: bool,
) -> None:
    """Typeset an EPUB or Markdown file using Pandoc and XeLaTeX."""
    suffix = ".tex" if tex else ".pdf"
    destination = output_path or input_path.with_name(
        f"{input_path.stem}-{size}{suffix}"
    )
    if destination.suffix.lower() != suffix:
        raise click.UsageError(f"output must end in {suffix}")
    try:
        render_book(
            input_path,
            destination,
            size=size,
            font=font,
            sans_font=sans_font,
            mono_font=mono_font,
            font_size=font_size,
            twoside=not one_sided,
            indent=indent,
            compile_pdf=not tex,
        )
    except (OSError, RuntimeError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    click.echo(f"Wrote {destination}")
