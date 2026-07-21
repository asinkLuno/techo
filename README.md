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
- **movie** — movie/TV rating page (74m5): searches [TMDB](https://www.themoviedb.org/) for the name, original name, and poster, prints five hollow stars to fill in, and adds midori-style 5 mm episode grids for TV shows — one cell per episode, many seasons packed onto each page.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) · XeLaTeX (TeX Live) · `3270 Nerd Font Mono`
- The `movie` command additionally needs a TMDB key (`TMDB_ACCESS_TOKEN` v4 or
  `TMDB_API_KEY` v3 env var) and a CJK font for zh-CN titles (`--cjk-font`, default `FZBaoSong-Z04S`).

## Build

```bash
uv run techo nightowl --size m5          # or cozyca, 74m5
uv run techo senary 2026-07              # calendar + tracker + day pages for the month
uv run techo movie "盗梦空间"             # rating page; default size 74m5
uv run techo movie "绝命毒师" --type tv   # rating page + packed season grids
uv run techo movie "X" --index 1         # pick the 2nd search result
uv run techo ebook extract book.epub      # EPUB → Markdown directory
uv run techo ebook split omnibus.epub     # omnibus → individual EPUB files
uv run techo ebook render book.epub --size a5s
uv run techo ebook render book.md --size a7l --tex
```

`senary` accepts `--tz` (IANA name, e.g. `Asia/Shanghai`) and
`--location` (default `tranquility`); a non-UTC `--tz` adds a UTC strip to day pages.

`movie` searches both movies and TV (use `--type movie|tv` to restrict), lists
matches, and picks the first by default (`--index N` to choose another).
`--no-compile` writes the LaTeX without running xelatex.

Book rendering additionally requires Pandoc. PDF output uses XeLaTeX; pass
`--tex` to stop after generating LaTeX.

## Structure

```
src/sizes.py                  # single source of truth for sizes → generates sizes.tex
src/cli.py                    # `techo` CLI — the single entry point
src/nightowl/night-owl.tex    # night-owl template (size via \EDITION)
src/movie/movie.{py,tex}      # movie/TV rating page (TMDB search + season grids)
src/senary/{senary,day}.tex   # senary (landscape m5) + day (portrait m5) templates
src/sizes.tex                 # generated (gitignored) — \Size{<size>}{PW|PH|RedLine}
<edition>/
├── <edition>.tex             # generated wrapper (gitignored)
├── content.tex               # generated page content (gitignored)
└── <edition>.pdf             # output (gitignored)
```

Add a new size by editing `src/sizes.py` (page geometry in `SIZES`, design-specific
layout in `NIGHTOWL`); the generators and templates pick it up.
