"""Post-process generated editions into print-ready spreads."""

from pathlib import Path

from . import build, sizes


def spread(edition: str, size: str, *, side: str = "outer", quiet: bool = True) -> Path:
    """Compile ``outputs/<edition>/<edition>.pdf`` into ``spread.pdf``."""
    s = sizes.SIZES[size]
    out = build.OUTPUTS / edition
    pdf = out / f"{edition}.pdf"
    if not pdf.exists():
        raise RuntimeError(f"no generated edition at {pdf}; generate it first")

    booklet = size in ("tn", "tnp")
    if booklet:
        include = f"\\includepdf[pages=-, booklet=true, landscape]{{{edition}.pdf}}"
    else:
        pages = "2,1" if side == "binding" else "1,2"
        include = (
            f"\\includepdf[pages={{{pages}}}, nup=2x1, "
            f"width={s['pw']}mm, height={s['ph']}mm]{{{edition}.pdf}}"
        )
    tex = (
        "\\documentclass[10pt]{article}\n"
        f"\\usepackage[paperwidth={s['pw'] * 2}mm, paperheight={s['ph']}mm, margin=0mm]{{geometry}}\n"
        "\\usepackage{pdfpages}\n"
        "\\begin{document}\n"
        f"{include}\n"
        "\\end{document}\n"
    )
    (out / "spread.tex").write_text(tex)
    build.compile_tex("spread.tex", out, quiet=quiet)
    return out / "spread.pdf"


def generate(edition: str, size: str, side: str = "outer") -> None:
    output = spread(edition, size, side=side)
    s = sizes.SIZES[size]
    print(f"Generated {output} ({s['pw'] * 2}×{s['ph']}mm spread)")
