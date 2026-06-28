# xianzhang — plain ruled notebooks

Two sizes:
- **a5s-xianzhang** — 110×210mm, blue 6mm lines, red margin at 12mm
- **m5-xianzhang** — 67×105mm, blue 6mm lines, red margin at 7mm

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- XeLaTeX (TeX Live)

## Build

```bash
uv run python xianzhang.py a5s-xianzhang && cd a5s-xianzhang && xelatex a5s-xianzhang.tex && xelatex a5s-xianzhang.tex
uv run python xianzhang.py m5-xianzhang  && cd m5-xianzhang  && xelatex m5-xianzhang.tex  && xelatex m5-xianzhang.tex
```

Output: `a5s-xianzhang/a5s-xianzhang.pdf`, `m5-xianzhang/m5-xianzhang.pdf`

## Structure

```
xianzhang/
├── sizes.tex                # shared size definitions (all dimensions)
├── xianzhang.py             # content generator (shared across sizes)
├── a5s-xianzhang/
│   ├── a5s-xianzhang.tex    # 110×210mm template
│   ├── content.tex          # generated (gitignored)
│   └── a5s-xianzhang.pdf    # output (gitignored)
└── m5-xianzhang/
    ├── m5-xianzhang.tex     # 67×105mm template
    ├── content.tex          # generated (gitignored)
    └── m5-xianzhang.pdf     # output (gitignored)
```
