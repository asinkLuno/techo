# techo — lunar planners

**Senary edition** — moon phase planner (110×210mm, 9mm binding offset, 171 pages).
**Xianzhang** — plain ruled notebook (110×210mm, blue 6mm lines, red margin at 12mm).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- XeLaTeX (TeX Live)

## Build

```bash
# Senary edition (moon phase planner)
PYTHONPATH=. uv run python senary/generate.py
cd senary && xelatex senary.tex && xelatex senary.tex

# Xianzhang (plain ruled notebook)
uv run python xianzhang/generate.py
cd xianzhang && xelatex xianzhang.tex && xelatex xianzhang.tex
```

Output: `senary/senary.pdf`, `xianzhang/xianzhang.pdf`

## Structure

```
techo/
├── moonlib.py           # shared moon phase calculation (ephem)
├── pyproject.toml       # uv project config
├── senary/
│   ├── senary.tex       # moon planner LaTeX template
│   ├── generate.py      # content generation (imports moonlib)
│   ├── moon-data.tex    # generated (gitignored)
│   ├── content.tex      # generated (gitignored)
│   └── senary.pdf       # output (gitignored)
├── xianzhang/
│   ├── xianzhang.tex    # ruled notebook LaTeX template
│   ├── generate.py      # content generation (standalone)
│   ├── content.tex      # generated (gitignored)
│   └── xianzhang.pdf    # output (gitignored)
└── .gitignore
```

## Adding a new edition

1. Create `edition/generate.py` importing `moonlib` (or standalone)
2. Create `edition/edition.tex` with desired geometry
3. Build: same pattern as above
