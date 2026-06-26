# techo — lunar planners

**Senary edition** (110×210mm, 9mm binding offset, 171 pages).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- XeLaTeX (TeX Live)

## Build

```bash
# Generate moon data + content
PYTHONPATH=. uv run python senary/generate.py

# Compile PDF (×2 for stable page numbers)
cd senary && xelatex senary.tex && xelatex senary.tex
```

Output: `senary/senary.pdf`

## Structure

```
techo/
├── moonlib.py           # shared moon phase calculation (ephem)
├── pyproject.toml       # uv project config
├── senary/
│   ├── senary.tex       # LaTeX template
│   ├── generate.py      # content generation
│   ├── moon-data.tex    # generated (gitignored)
│   ├── content.tex      # generated (gitignored)
│   └── senary.pdf       # output (gitignored)
└── .gitignore
```

## Adding a new edition

1. Create `edition/generate.py` importing `moonlib`
2. Create `edition/edition.tex` with desired geometry
3. Build: same pattern as senary
