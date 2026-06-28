# xianzhang — plain ruled notebooks

- **xianzhang-a5s** — 110×210mm, blue 6mm lines, red margin at 12mm
- **xianzhang-m5** — 67×105mm, blue 6mm lines, red margin at 7mm

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- XeLaTeX (TeX Live)

## Build

```bash
uv run python xianzhang.py xianzhang-a5s && cd xianzhang-a5s && xelatex xianzhang-a5s.tex && xelatex xianzhang-a5s.tex
uv run python xianzhang.py xianzhang-m5  && cd xianzhang-m5  && xelatex xianzhang-m5.tex  && xelatex xianzhang-m5.tex
```

## Structure

```
xianzhang/
├── sizes.tex              # shared size definitions
├── xianzhang.py           # content generator
├── xianzhang-a5s/
│   ├── xianzhang-a5s.tex  # 110×210mm
│   ├── content.tex        # generated (gitignored)
│   └── xianzhang-a5s.pdf  # output (gitignored)
└── xianzhang-m5/
    ├── xianzhang-m5.tex   # 67×105mm
    ├── content.tex        # generated (gitignored)
    └── xianzhang-m5.pdf   # output (gitignored)
```
