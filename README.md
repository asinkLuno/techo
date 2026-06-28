# techo — lunar planners

**Senary edition** — moon phase planner (110×210mm, 9mm binding offset, 171 pages).
**Xianzhang** — plain ruled notebook, two sizes:
- **a5s** — 110×210mm, blue 6mm lines, red margin at 12mm
- **m5** — 67×105mm, blue 6mm lines, red margin at 7mm

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- XeLaTeX (TeX Live)

## Build

```bash
# Senary edition (moon phase planner)
PYTHONPATH=. uv run python senary/generate.py
cd senary && xelatex senary.tex && xelatex senary.tex

# Xianzhang a5s (110×210mm)
uv run python xianzhang/generate.py
cd xianzhang && xelatex xianzhang.tex && xelatex xianzhang.tex

# Xianzhang m5 (67×105mm)
uv run python m5/generate.py
cd m5 && xelatex m5.tex && xelatex m5.tex
```

Output: `senary/senary.pdf`, `xianzhang/xianzhang.pdf`, `m5/m5.pdf`

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
│   ├── xianzhang.tex    # ruled notebook a5s (110×210mm)
│   ├── generate.py      # content generation (standalone)
│   ├── content.tex      # generated (gitignored)
│   └── xianzhang.pdf    # output (gitignored)
├── m5/
│   ├── m5.tex           # ruled notebook m5 (67×105mm)
│   ├── generate.py      # content generation (standalone)
│   ├── content.tex      # generated (gitignored)
│   └── m5.pdf           # output (gitignored)
└── .gitignore
```

## Adding a new edition

1. Create `edition/generate.py` importing `moonlib` (or standalone)
2. Create `edition/edition.tex` with desired geometry
3. Build: same pattern as above
