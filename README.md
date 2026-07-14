# techo — printable paper and book generator (Python + XeLaTeX)

One `techo` CLI generates notebook pages and print-ready books. Notebook
generators write per-edition `content.tex` plus a size-specific wrapper; shared
LaTeX templates do the rest.

The `ebook` command group also extracts EPUB files, splits omnibus editions,
and typesets EPUB or Markdown books for any paper size defined in `src/sizes.py`.

## Designs & sizes

| size | mm | night-owl | senary |
|------|----|-----------|--------|
| cozyca | 100×90 | ✓ | |
| m5 | 67×105 | ✓ | |
| 74m5 | 74×105 | ✓ | |
| m5l | 105×67 | | ✓ |

- **night-owl** — numbers 0–26 in a triangular hourglass over a dot grid (3270 Nerd Font).
- **senary** — monthly calendar (front) + habit tracker (back) + day pages (portrait m5, batch-generated for the whole month); landscape m5l, takes `YYYY-MM`.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) · XeLaTeX (TeX Live) · `3270 Nerd Font Mono`

## Build

```bash
uv run techo nightowl --size m5          # or cozyca, 74m5
uv run techo senary 2026-07              # calendar + tracker + day pages for the month
uv run techo ebook extract book.epub      # EPUB → Markdown directory
uv run techo ebook split omnibus.epub     # omnibus → individual EPUB files
uv run techo ebook render book.epub --size a5s
uv run techo ebook render book.md --size a7l --tex
```

`senary` accepts `--tz` (IANA name, e.g. `Asia/Shanghai`) and
`--location` (default `tranquility`); a non-UTC `--tz` adds a UTC strip to day pages.

Book rendering additionally requires Pandoc. PDF output uses XeLaTeX; pass
`--tex` to stop after generating LaTeX.

## Structure

```
src/sizes.py                  # single source of truth for sizes → generates sizes.tex
src/cli.py                    # `techo` CLI — the single entry point
src/nightowl/night-owl.tex    # night-owl template (size via \EDITION)
src/senary/{senary,day}.tex   # senary (landscape m5) + day (portrait m5) templates
src/sizes.tex                 # generated (gitignored) — \Size{<size>}{PW|PH|RedLine}
<edition>/
├── <edition>.tex             # generated wrapper (gitignored)
├── content.tex               # generated page content (gitignored)
└── <edition>.pdf             # output (gitignored)
```

Add a new size by editing `src/sizes.py` (page geometry in `SIZES`, design-specific
layout in `NIGHTOWL`); the generators and templates pick it up.
