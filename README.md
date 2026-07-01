# techo — printable notebook page generator (Python + XeLaTeX)

Three outputs, one `techo` CLI. Each generator writes per-edition `content.tex`
+ a size-specific wrapper into an edition directory; the shared LaTeX template
does the rest.

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
```

`senary` accepts `--tz` (IANA name, e.g. `Asia/Shanghai`) and
`--location` (default `tranquility`); a non-UTC `--tz` adds a UTC strip to day pages.

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
