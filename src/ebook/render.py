"""Pandoc and XeLaTeX book rendering."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..sizes import SIZES

FONT_ALIASES = {
    "bs": "FZBaoSong-Z04S",
    "cyly": "ChenYuluoyan 2.0",
    "jhls": "KingHwaOldSong",
}


def _require(program: str) -> None:
    if shutil.which(program) is None:
        raise RuntimeError(f"Required program not found: {program}")


def _header(
    *,
    font: str,
    sans_font: str,
    mono_font: str,
    width: int,
    height: int,
    twoside: bool,
    indent: str | None,
) -> str:
    geometry = f"paperwidth={width}mm,paperheight={height}mm,margin=12mm"
    footer = r"\fancyfoot[C]{\footnotesize\thepage}"
    if twoside:
        geometry += ",twoside,inner=16mm,outer=10mm"
        footer = r"\fancyfoot[LE,RO]{\footnotesize\thepage}"
    paragraph = r"\raggedright"
    if indent and indent != "none":
        paragraph += f"\n\\setlength{{\\parindent}}{{{indent}}}"
    return rf"""\usepackage{{scrextend}}
\usepackage{{fontspec}}
\setmainfont{{{font}}}
\usepackage{{xeCJK}}
\setCJKmainfont{{{font}}}
\setCJKsansfont{{{sans_font}}}
\setCJKmonofont{{{mono_font}}}
{paragraph}
\usepackage[{geometry}]{{geometry}}
\usepackage{{fancyhdr}}
\pagestyle{{fancy}}
\fancyhf{{}}
\renewcommand{{\headrulewidth}}{{0pt}}
{footer}
"""


def render_book(
    input_path: Path,
    output_path: Path,
    *,
    size: str,
    font: str,
    sans_font: str,
    mono_font: str,
    font_size: str,
    twoside: bool,
    indent: str | None,
    compile_pdf: bool,
) -> Path:
    """Render one EPUB or Markdown file to a standalone TeX or PDF file."""
    _require("pandoc")
    if compile_pdf:
        _require("xelatex")
    if input_path.suffix.lower() not in {".epub", ".md", ".markdown"}:
        raise ValueError("input must be EPUB or Markdown")
    if size not in SIZES:
        raise ValueError(f"unknown page size: {size}")

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page = SIZES[size]
    font = FONT_ALIASES.get(font, font)
    with tempfile.TemporaryDirectory(prefix="techo-ebook-") as temporary:
        work = Path(temporary)
        header = work / "header.tex"
        header.write_text(
            _header(
                font=font,
                sans_font=sans_font,
                mono_font=mono_font,
                width=page["pw"],
                height=page["ph"],
                twoside=twoside,
                indent=indent,
            ),
            encoding="utf-8",
        )
        tex = work / "book.tex"
        source_format = "epub" if input_path.suffix.lower() == ".epub" else "markdown"
        class_options = f"UTF8,fontsize={font_size}" + (
            ",twoside,openright" if twoside else ""
        )
        command = [
            "pandoc",
            str(input_path.resolve()),
            "-f",
            source_format,
            "-V",
            "documentclass=ctexbook",
            "-V",
            f"classoption={class_options}",
            f"--include-in-header={header}",
            "--toc",
            "--toc-depth=2",
            "-s",
            "-M",
            "title=",
            "-M",
            "author=",
            "-M",
            "date=",
            "-o",
            str(tex),
        ]
        media = output_path.with_name(f"{output_path.stem}_media")
        command.append(f"--extract-media={work / 'media' if compile_pdf else media}")
        subprocess.run(command, check=True)
        tex.write_text(
            tex.read_text(encoding="utf-8").replace("\r", ""), encoding="utf-8"
        )

        if not compile_pdf:
            shutil.copy2(tex, output_path)
            return output_path
        for _ in range(2):
            subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                cwd=work,
                check=True,
                stdout=subprocess.DEVNULL,
            )
        shutil.copy2(tex.with_suffix(".pdf"), output_path)
    return output_path
