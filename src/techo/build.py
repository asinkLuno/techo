"""Shared build layer for edition generators.

Every generator used to repeat the same "output dir + content.tex + wrapper
tex + xelatex" sequence (and each had its own copy of the spread.tex /
booklet assembly).  This module centralises that boilerplate:

* ``compile_tex`` — the single xelatex invocation (nonstop mode, quiet,
  configurable pass count; single-page editions need only one pass).
* ``build_edition`` — writes sizes.tex, the content.tex body, the wrapper
  tex (``\\def`` preamble + ``\\input`` of the template) and compiles it.
"""

import subprocess
from pathlib import Path

from . import sizes

OUTPUTS = Path("outputs")


def compile_tex(tex_file: str, cwd: Path, *, passes: int = 1, quiet: bool = True) -> None:
    """Run xelatex ``passes`` times in ``cwd``, failing loudly on errors.

    ``-interaction=nonstopmode -halt-on-error`` keeps batch builds from
    hanging on a prompt; ``quiet`` silences the (usually huge) log.
    Multi-pass documents (TOC / cross-references, e.g. ebook) pass
    ``passes=2``; single-page editions default to one pass.
    """
    for _ in range(passes):
        subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_file],
            cwd=cwd,
            check=True,
            stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.DEVNULL if quiet else None,
        )


def build_edition(
    edition: str,
    content: str | list[str] | None,
    template: str,
    *,
    defs: dict[str, object] | None = None,
    passes: int = 1,
    compile: bool = True,
    quiet: bool = True,
) -> Path:
    """Write sizes.tex + content.tex + wrapper tex, then compile the edition.

    ``edition`` is the output directory name under ``outputs/`` and the
    wrapper's basename (``{edition}.tex``).  ``content`` (list of lines or
    a single string) is written to ``content.tex``; ``None`` skips it
    (templates that build everything from the wrapper defs, e.g. tn-cover).
    ``template`` is the ``\\input`` target of the wrapper.  ``defs`` become
    ``\\def\\NAME{value}%`` lines before the input (``EDITION``, margins,
    fonts, …).

    Returns the output directory.
    """
    sizes.write_sizes_tex()
    out = OUTPUTS / edition
    out.mkdir(parents=True, exist_ok=True)
    if content is not None:
        body = content if isinstance(content, str) else "\n".join(content)
        if not body.endswith("\n"):
            body += "\n"
        (out / "content.tex").write_text(body)
    wrapper = "".join(f"\\def\\{name}{{{value}}}%\n" for name, value in (defs or {}).items())
    wrapper += f"\\input{{{template}}}%\n"
    (out / f"{edition}.tex").write_text(wrapper)
    if compile:
        compile_tex(f"{edition}.tex", out, passes=passes, quiet=quiet)
    return out
