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

# Xianzhang (ruled notebook, all sizes share xgen.py)
uv run python xgen.py a5s && cd a5s && xelatex a5s.tex && xelatex a5s.tex
uv run python xgen.py m5  && cd m5  && xelatex m5.tex  && xelatex m5.tex
```

Output: `senary/senary.pdf`, `a5s/a5s.pdf`, `m5/m5.pdf`

## Structure

```
techo/
├── moonlib.py           # shared moon phase calculation (ephem)
├── xgen.py              # shared ruled notebook generator (all sizes)
├── pyproject.toml       # uv project config
├── senary/
│   ├── senary.tex       # moon planner LaTeX template
│   ├── generate.py      # content generation (imports moonlib)
│   ├── moon-data.tex    # generated (gitignored)
│   ├── content.tex      # generated (gitignored)
│   └── senary.pdf       # output (gitignored)
├── a5s/
│   ├── a5s.tex          # ruled notebook (110×210mm)
│   ├── content.tex      # generated (gitignored)
│   └── a5s.pdf          # output (gitignored)
├── m5/
│   ├── m5.tex           # ruled notebook (67×105mm)
│   ├── content.tex      # generated (gitignored)
│   └── m5.pdf           # output (gitignored)
└── .gitignore
```

## Adding a new xianzhang size

1. Create `<size>/<size>.tex` with desired geometry (paper size, red line, line count)
2. Build: `uv run python xgen.py <size> && cd <size> && xelatex <size>.tex`
