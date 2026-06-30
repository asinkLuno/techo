# techo — printable notebook page generator (Python + XeLaTeX)

Three designs, three page sizes. Each generator writes per-edition `content.tex`
+ a size-specific wrapper into an edition directory; the shared template at the
repo root does the rest.

## Designs & sizes

| size | mm | night-owl | xianzhang | senary |
|------|----|-----------|-----------|--------|
| cozyca | 100×90 | ✓ | ✓ | |
| m5 | 67×105 | ✓ | ✓ | |
| m5l | 105×67 | | | ✓ |
| a5s | 110×210 | | ✓ | |

- **night-owl** — numbers 0–26 in a triangular hourglass over a dot grid (3270 Nerd Font).
- **xianzhang** — French ruled (Séyès) lines with a red margin.
- **senary** — monthly calendar (front) + habit tracker (back); landscape m5 (105×67), takes `YYYY-MM`.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) · XeLaTeX (TeX Live) · `3270 Nerd Font Mono`

## Build

```bash
# night-owl
uv run python nightowl.py --size m5      && cd night-owl-m5      && xelatex night-owl-m5.tex      && xelatex night-owl-m5.tex
uv run python nightowl.py --size cozyca  && cd night-owl-cozyca  && xelatex night-owl-cozyca.tex  && xelatex night-owl-cozyca.tex

# xianzhang
uv run python xianzhang.py xianzhang-m5      && cd xianzhang-m5      && xelatex xianzhang-m5.tex      && xelatex xianzhang-m5.tex
uv run python xianzhang.py xianzhang-cozyca  && cd xianzhang-cozyca  && xelatex xianzhang-cozyca.tex  && xelatex xianzhang-cozyca.tex
uv run python xianzhang.py xianzhang-a5s     && cd xianzhang-a5s     && xelatex xianzhang-a5s.tex     && xelatex xianzhang-a5s.tex

# senary
uv run python senary.py 2026-07 && cd senary-2026-07 && xelatex senary-2026-07.tex && xelatex senary-2026-07.tex
```

## Structure

```
sizes.py             # single source of truth for sizes → generates sizes.tex
night-owl.tex        # shared night-owl template (size via \EDITION)
xianzhang.tex        # shared xianzhang template (size via \EDITION)
nightowl.py          # night-owl generator
xianzhang.py         # xianzhang generator
senary.py            # senary generator (calendar + habit tracker, landscape m5)
sizes.tex            # generated (gitignored) — \Size{<size>}{PW|PH|RedLine}
<edition>/
├── <edition>.tex    # generated wrapper (gitignored): \def\EDITION{…}\input{../<design>.tex}
├── content.tex      # generated page content (gitignored)
└── <edition>.pdf    # output (gitignored)
```

Add a new size by editing `sizes.py` (page geometry in `SIZES`, design-specific
layout in `NIGHTOWL` / `XIANZHANG`); the generators and templates pick it up.
