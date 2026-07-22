"""Single source of truth for notebook sizes (mm) and fonts (pt).

Imported by both generators; `write_sizes_tex()` emits `sizes.tex` for the
LaTeX templates. Edit sizes here — never hand-edit sizes.tex.
"""

import subprocess
from pathlib import Path
from typing import TypedDict


class PageSize(TypedDict):
    """Physical page dimensions, in millimetres."""

    pw: float
    ph: float
    red_line: float


class GreenDotLayout(TypedDict):
    binding: float
    right_margin: float
    top_margin: float
    bottom_margin: float


class NightOwlLayout(TypedDict):
    binding: float
    right_margin: float
    row_gap: float
    num_gap: float


class MidoriGridLayout(TypedDict):
    binding: float
    right_margin: float
    top_margin: float
    bottom_margin: float
    grid_step: float
    dot_freq: int
    gap_size: float
    edge_extension: float


class MovieReportLayout(TypedDict):
    bind: float  # inner / binding margin, mm
    outer: float  # outer margin, mm
    poster_w: float  # poster slot width, mm
    poster_h: float  # poster slot height, mm
    stamp_w: float  # width of one EP/SEEN stamp (column calc), mm
    circle_size: float  # checkbox circle diameter, mm
    dateblank_seg: float  # width of one date-blank segment, mm
    gap: float  # partial-row gap in _spread_grid, mm
    raisebox_offset: float  # \raisebox offset for \epitem/\seenitem, pt
    title_pt: float  # title font size, pt
    label_pt: float  # EP01 / SEEN / date-blank font size, pt
    caplabel_pt: float  # section-header caps label font size, pt
    stamp_pt: float  # datestamp / filestamp font size, pt
    footer_pt: float  # footer ref-code font size, pt
    letterspace: float  # \capfont LetterSpace (percent of font size)
    dither_px: float  # target longer-side px for Bayer dither pre-scale
    card_head_gap: float  # vspace between card header and its rule, pt
    card_rule_gap: float  # vspace between card rule and body, pt


# ── Page geometry + red margin (consumed by LaTeX templates via \Size) ──
SIZES: dict[str, PageSize] = {
    "cozyca": {"pw": 100, "ph": 90, "red_line": 8},
    "62m5": {"pw": 62, "ph": 105, "red_line": 13},
    "67m5": {"pw": 67, "ph": 105, "red_line": 13},
    "67m5l": {"pw": 105, "ph": 67, "red_line": 8},  # landscape m5 (senary)
    "74m5": {"pw": 74, "ph": 105, "red_line": 12},
    "a4": {"pw": 210, "ph": 297, "red_line": 20},
    "b5": {"pw": 176, "ph": 250, "red_line": 18},
    "a5": {"pw": 148, "ph": 210, "red_line": 15},
    "a5fc": {"pw": 107, "ph": 172, "red_line": 12},
    "a6per": {"pw": 95, "ph": 172, "red_line": 12},
    "a6s": {"pw": 80, "ph": 172, "red_line": 10},
    "a6standard": {"pw": 105, "ph": 148, "red_line": 12},
    "127a7": {"pw": 80, "ph": 127, "red_line": 10},
    "a7l": {"pw": 85, "ph": 127, "red_line": 10},
    "120a7": {"pw": 80, "ph": 120, "red_line": 10},
    "a5s": {"pw": 110, "ph": 210, "red_line": 15},
    "tn": {"pw": 110, "ph": 210, "red_line": 15},
    "tnp": {"pw": 88, "ph": 125, "red_line": 10},
}

GREEN_DOT: dict[str, GreenDotLayout] = {
    "cozyca": {"binding": 15, "right_margin": 3, "top_margin": 10, "bottom_margin": 10},
    "62m5": {"binding": 12, "right_margin": 3, "top_margin": 10, "bottom_margin": 10},
    "67m5": {"binding": 12, "right_margin": 3, "top_margin": 10, "bottom_margin": 10},
    "67m5l": {"binding": 10, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    "74m5": {"binding": 12, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    "a4": {"binding": 20, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    "b5": {"binding": 18, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    "a5": {"binding": 15, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    "a5fc": {"binding": 12, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    "a6per": {"binding": 12, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    "a6s": {"binding": 10, "right_margin": 3, "top_margin": 10, "bottom_margin": 10},
    "a6standard": {
        "binding": 12,
        "right_margin": 5,
        "top_margin": 10,
        "bottom_margin": 10,
    },
    "127a7": {"binding": 10, "right_margin": 3, "top_margin": 10, "bottom_margin": 10},
    "120a7": {"binding": 10, "right_margin": 3, "top_margin": 10, "bottom_margin": 10},
    "a5s": {"binding": 15, "right_margin": 5, "top_margin": 10, "bottom_margin": 10},
    "tn": {"binding": 3, "right_margin": 3, "top_margin": 3, "bottom_margin": 3},
    "tnp": {"binding": 3, "right_margin": 3, "top_margin": 3, "bottom_margin": 3},
}

NIGHTOWL: dict[str, NightOwlLayout] = {
    "cozyca": {"binding": 15, "right_margin": 3, "row_gap": 7.5, "num_gap": 16},
    "62m5": {"binding": 12, "right_margin": 3, "row_gap": 8.0, "num_gap": 10},
    "67m5": {"binding": 12, "right_margin": 3, "row_gap": 8.0, "num_gap": 11},
    "74m5": {"binding": 12, "right_margin": 3, "row_gap": 8.0, "num_gap": 13},
    "a4": {"binding": 20, "right_margin": 5, "row_gap": 14.0, "num_gap": 42},
    "b5": {"binding": 18, "right_margin": 5, "row_gap": 14.0, "num_gap": 35},
    "a5": {"binding": 15, "right_margin": 5, "row_gap": 14.0, "num_gap": 29},
    "a5fc": {"binding": 12, "right_margin": 5, "row_gap": 10.0, "num_gap": 21},
    "a6per": {"binding": 12, "right_margin": 5, "row_gap": 10.0, "num_gap": 18},
    "a6s": {"binding": 10, "right_margin": 3, "row_gap": 10.0, "num_gap": 15},
    "a6standard": {"binding": 12, "right_margin": 5, "row_gap": 10.0, "num_gap": 20},
    "127a7": {"binding": 10, "right_margin": 3, "row_gap": 8.0, "num_gap": 15},
    "120a7": {"binding": 10, "right_margin": 3, "row_gap": 8.0, "num_gap": 15},
    "a5s": {"binding": 18, "right_margin": 5, "row_gap": 14.0, "num_gap": 26},
}

MIDORI_GRID: dict[str, MidoriGridLayout] = {
    "cozyca": {
        "binding": 15,
        "right_margin": 3,
        "top_margin": 5,
        "bottom_margin": 5,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.2,
        "edge_extension": 1.5,
    },
    "62m5": {
        "binding": 12,
        "right_margin": 3,
        "top_margin": 5,
        "bottom_margin": 5,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.0,
        "edge_extension": 1.2,
    },
    "67m5": {
        "binding": 12,
        "right_margin": 3,
        "top_margin": 5,
        "bottom_margin": 5,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.0,
        "edge_extension": 1.2,
    },
    "74m5": {
        "binding": 12,
        "right_margin": 5,
        "top_margin": 4,
        "bottom_margin": 9,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.0,
        "edge_extension": 1.2,
    },
    "67m5l": {
        "binding": 10,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 5,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.2,
        "edge_extension": 1.5,
    },
    "a4": {
        "binding": 20,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.5,
        "edge_extension": 2.0,
    },
    "b5": {
        "binding": 18,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.5,
        "edge_extension": 2.0,
    },
    "a5": {
        "binding": 15,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.2,
        "edge_extension": 1.5,
    },
    "a5fc": {
        "binding": 12,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.2,
        "edge_extension": 1.5,
    },
    "a6per": {
        "binding": 12,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.0,
        "edge_extension": 1.2,
    },
    "a6s": {
        "binding": 10,
        "right_margin": 3,
        "top_margin": 5,
        "bottom_margin": 5,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.0,
        "edge_extension": 1.2,
    },
    "a6standard": {
        "binding": 12,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.0,
        "edge_extension": 1.2,
    },
    "127a7": {
        "binding": 10,
        "right_margin": 3,
        "top_margin": 5,
        "bottom_margin": 5,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.0,
        "edge_extension": 1.2,
    },
    "120a7": {
        "binding": 10,
        "right_margin": 3,
        "top_margin": 5,
        "bottom_margin": 5,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.0,
        "edge_extension": 1.2,
    },
    "a5s": {
        "binding": 15,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.2,
        "edge_extension": 1.5,
    },
    "tn": {
        "binding": 5,
        "right_margin": 5,
        "top_margin": 10,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.2,
        "edge_extension": 1.5,
    },
    "tnp": {
        "binding": 5,
        "right_margin": 5,
        "top_margin": 5,
        "bottom_margin": 10,
        "grid_step": 5,
        "dot_freq": 10,
        "gap_size": 1.2,
        "edge_extension": 1.5,
    },
}

# ── Movie Report layout ──
MOVIE_REPORT: dict[str, MovieReportLayout] = {
    "cozyca": {
        "bind": 15,
        "outer": 3,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "62m5": {
        "bind": 12,
        "outer": 3,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "67m5": {
        "bind": 12,
        "outer": 3,
        "poster_w": 27,
        "poster_h": 41,
        "stamp_w": 15,
        "circle_size": 3.2,
        "dateblank_seg": 2.0,
        "gap": 2.5,
        "raisebox_offset": 4.0,
        "title_pt": 12,
        "label_pt": 5.5,
        "caplabel_pt": 5.5,
        "stamp_pt": 7.5,
        "footer_pt": 6.0,
        "letterspace": 32,
        "dither_px": 130,
        "card_head_gap": 2,
        "card_rule_gap": 4,
    },
    "67m5l": {
        "bind": 10,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 2,
        "card_rule_gap": 4,
    },
    "74m5": {
        "bind": 12,
        "outer": 5,
        "poster_w": 30,
        "poster_h": 45,
        "stamp_w": 16,
        "circle_size": 3.5,
        "dateblank_seg": 2.2,
        "gap": 2.5,
        "raisebox_offset": 4.5,
        "title_pt": 13,
        "label_pt": 6,
        "caplabel_pt": 6.0,
        "stamp_pt": 8.0,
        "footer_pt": 6.5,
        "letterspace": 35,
        "dither_px": 140,
        "card_head_gap": 2,
        "card_rule_gap": 4,
    },
    "a4": {
        "bind": 20,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "b5": {
        "bind": 18,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "a5": {
        "bind": 15,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "a5fc": {
        "bind": 12,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "a6per": {
        "bind": 12,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "a6s": {
        "bind": 10,
        "outer": 3,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "a6standard": {
        "bind": 12,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "127a7": {
        "bind": 10,
        "outer": 3,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "a7l": {
        "bind": 10,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "120a7": {
        "bind": 10,
        "outer": 3,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "a5s": {
        "bind": 15,
        "outer": 5,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "tn": {
        "bind": 3,
        "outer": 3,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
    "tnp": {
        "bind": 3,
        "outer": 3,
        "poster_w": 42,
        "poster_h": 63,
        "stamp_w": 24,
        "circle_size": 5.5,
        "dateblank_seg": 3.8,
        "gap": 4.0,
        "raisebox_offset": 6.5,
        "title_pt": 16,
        "label_pt": 7,
        "caplabel_pt": 7.5,
        "stamp_pt": 10,
        "footer_pt": 6.5,
        "letterspace": 45,
        "dither_px": 200,
        "card_head_gap": 3,
        "card_rule_gap": 6,
    },
}

# ── Font sizes in pt ──
FONTS = {
    "large": 12,
    "medium": 9,
    "small": 8,
    "tiny": 5,
}

# ── Colors (single source of truth, emitted to sizes.tex) ──
COLORS = {
    "IronOxideRed": "8b0000",
    "ChromeYellow": "ffa700",
    "CobaltBlue": "0047ab",
    "NeonGreen": "39FF14",
}

FONT_CMD = {k: f"Font{k.title()}" for k in FONTS}


def write_sizes_tex(path: Path | None = None) -> None:
    """Emit sizes.tex exposing page sizes, red lines, and font commands."""
    if path is None:
        path = Path(__file__).parent / "sizes.tex"
    lines = [
        r"% Generated by sizes.py — do not edit; edit sizes.py",
        r"\def\Size#1#2{\csname size@#1@#2\endcsname}",
    ]
    for key, s in SIZES.items():
        for field, val in (
            ("PW", s["pw"]),
            ("PH", s["ph"]),
            ("RedLine", s["red_line"]),
        ):
            lines.append(
                rf"\expandafter\def\csname size@{key}@{field}\endcsname{{{val}}}"
            )
    lines.append("")
    lines.append(r"% Movie Report layout fields (mm / pt)")
    for key, m in MOVIE_REPORT.items():
        for field, val in (
            ("Bind", m["bind"]),
            ("Outer", m["outer"]),
            ("PosterW", m["poster_w"]),
            ("PosterH", m["poster_h"]),
            ("StampW", m["stamp_w"]),
            ("CircleSize", m["circle_size"]),
            ("DateblankSeg", m["dateblank_seg"]),
            ("Gap", m["gap"]),
            ("Raisebox", m["raisebox_offset"]),
            ("TitlePt", m["title_pt"]),
            ("LabelPt", m["label_pt"]),
            ("CaplabelPt", m["caplabel_pt"]),
            ("StampPt", m["stamp_pt"]),
            ("FooterPt", m["footer_pt"]),
            ("LetterSpace", m["letterspace"]),
            ("CardHeadGap", m["card_head_gap"]),
            ("CardRuleGap", m["card_rule_gap"]),
        ):
            lines.append(
                rf"\expandafter\def\csname size@{key}@{field}\endcsname{{{val}}}"
            )
    lines.append("")
    lines.append(r"% Font size commands (pt / leading)")
    for key, size in FONTS.items():
        leading = size * 1.2
        lines.append(
            rf"\def\{FONT_CMD[key]}"
            rf"{{\fontsize{{{size}pt}}{{{leading:.1f}pt}}\selectfont}}"
        )
    path.write_text("\n".join(lines) + "\n")
    write_colors_tex()


def write_colors_tex(path: Path | None = None) -> None:
    r"""Emit colors.tex with \definecolor for every color in COLORS."""
    if path is None:
        path = Path(__file__).parent / "colors.tex"
    lines = [r"% Generated by sizes.py — do not edit; edit sizes.py"]
    for name, hex_val in COLORS.items():
        lines.append(rf"\definecolor{{{name}}}{{HTML}}{{{hex_val}}}")
    path.write_text("\n".join(lines) + "\n")


def compile(tex_file: str, cwd: Path) -> None:
    """Run xelatex twice."""
    for _ in range(2):
        subprocess.run(["xelatex", tex_file], cwd=cwd, check=True)


if __name__ == "__main__":
    write_sizes_tex()
    print("Generated sizes.tex")
