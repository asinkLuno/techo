"""Senary edition — generate LaTeX content for 110×210mm bound planner.

Usage: uv run python senary/generate.py
Output: senary/moon-data.tex, senary/content.tex
"""

import calendar
import ephem
from datetime import date, timedelta
from pathlib import Path

from moonlib import DAY_NAMES, MONTH_NAMES, YEAR, date_str, iter_moon

HERE = Path(__file__).parent


def generate_data_macros() -> str:
    """Generate data macros: \\moon@phase@<date>, etc."""
    lines = [
        f"% Auto-generated moon phase data for {YEAR}",
        "% Accessed via: \\csname moon@phase@YYYY-MM-DD\\endcsname etc.",
        "",
    ]
    for d, phase, illum, name in iter_moon(YEAR):
        iso = date_str(d)
        lines.append(
            f"\\expandafter\\def\\csname moon@phase@{iso}\\endcsname{{{phase:.6f}}}"
        )
        lines.append(
            f"\\expandafter\\def\\csname moon@illum@{iso}\\endcsname{{{illum:.4f}}}"
        )
        lines.append(
            f"\\expandafter\\def\\csname moon@name@{iso}\\endcsname{{{name}}}"
        )
    return "\n".join(lines) + "\n"


def generate_month_grid(year: int, month: int) -> str:
    """Generate month calendar as SINGLE tikzpicture — title + grid + cells."""
    month_name = MONTH_NAMES[month - 1]
    days_in_month = calendar.monthrange(year, month)[1]
    first_dow = date(year, month, 1).weekday()  # 0=Mon

    CW = 12.4  # cell width mm
    CH = 11.0  # cell height mm
    TITLE_Y = 8  # mm above grid for title
    HEADER_Y = -5  # mm below title for DOW labels
    GRID_TOP = 0  # grid starts here
    ICON_OFF = 3.5  # icon offset from cell top
    NUM_OFF = 9.0  # day number offset from cell top

    rows = 0
    day = 1
    for week in range(6):
        if day > days_in_month:
            rows = week
            break
        day += 7
    grid_h = CH * rows

    lines = [
        f"\\begin{{tikzpicture}}",
        f"  % Title",
        f"  \\node[ink, font=\\large\\bfseries, anchor=north] "
        f"at (43.5mm, {TITLE_Y}mm) {{{month_name} {year}}};",
    ]

    # Day-of-week headers
    for i, name in enumerate(DAY_NAMES):
        cx = CW * i + CW / 2
        color = "accent" if i >= 5 else "ink"
        lines.append(
            f"  \\node[{color}, font=\\footnotesize\\bfseries] "
            f"at ({cx}mm, {HEADER_Y}mm) {{{name}}};"
        )

    # Grid
    lines.append(
        f"  \\draw[step={CW}mm, ink!30] (0,{GRID_TOP}mm) "
        f"grid (87mm, {GRID_TOP - grid_h}mm);"
    )

    # Day cells — inline moon drawing (no nested tikzpicture!)
    day = 1
    moon = ephem.Moon()
    for week in range(rows):
        for dow in range(7):
            if (week == 0 and dow < first_dow) or day > days_in_month:
                if day > days_in_month:
                    break
                continue
            d = date(year, month, day)
            moon.compute(d.strftime("%Y/%m/%d 12:00"))
            phase = float(moon.moon_phase)  # type: ignore[attr-defined]
            color = "accent" if dow >= 5 else "ink"
            cx = CW * dow + CW / 2
            cy = GRID_TOP - (CH * week + ICON_OFF)
            num_y = GRID_TOP - (CH * week + NUM_OFF)
            r = 2.5  # radius in mm
            term = r - phase * 4 * r
            lines.append(f"  % Day {day}")
            lines.append(
                f"  \\fill[black!12] ({cx - r}mm, {cy - r}mm) circle ({r}mm);"
            )
            lines.append(f"  \\begin{{scope}}")
            lines.append(
                f"    \\clip ({cx - r}mm, {cy - r}mm) circle ({r}mm);"
            )
            lines.append(
                f"    \\fill[moon-yellow] ({cx + term}mm, {cy - r}mm) "
                f"rectangle ({cx + r}mm, {cy + r}mm);"
            )
            lines.append(f"  \\end{{scope}}")
            lines.append(
                f"  \\draw[ink, thin] ({cx - r}mm, {cy - r}mm) circle ({r}mm);"
            )
            lines.append(
                f"  \\node[{color}, font=\\footnotesize] "
                f"at ({cx}mm, {num_y}mm) {{{day}}};"
            )
            day += 1

    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


def generate_week_pages() -> str:
    """Generate week planning pages for all weeks that overlap YEAR."""
    out = []
    jan1 = date(YEAR, 1, 1)
    mon = jan1 - timedelta(days=jan1.weekday())  # 0=Mon
    dec31 = date(YEAR, 12, 31)

    week_num = 0
    cursor = mon
    while cursor <= dec31:
        week_num += 1
        week_days = []
        for i in range(7):
            d = cursor + timedelta(days=i)
            in_year = d.year == YEAR
            week_days.append((d, in_year))

        days_in_year = [wd for wd in week_days if wd[1]]
        if not days_in_year:
            cursor += timedelta(days=7)
            continue

        first_day = days_in_year[0][0]
        last_day = days_in_year[-1][0]
        label = (
            f"Week {week_num}: "
            f"{first_day.strftime('%b %-d')} – "
            f"{last_day.strftime('%b %-d, %Y')}"
        )

        out.append("\\clearpage")
        out.append("\\vspace{2mm}")
        out.append(f"{{\\large\\textbf{{{label}}}}}\\par")
        out.append("\\vspace{2mm}")

        # All 7 days flow naturally — no forced page break mid-week
        all_days = [wd for wd in week_days if wd[1]]
        for i, (d, _) in enumerate(all_days):
            iso = date_str(d)
            out.append(_generate_day_slot(d, iso))
            if i < len(all_days) - 1:
                out.append("\\vspace{1.5mm}")

        # Notes section
        out.append("\\vspace{2mm}")
        out.append("{\\small\\textbf{Notes}}")
        out.append("\\vspace{1mm}")
        for _ in range(4):
            out.append("\\notesline")

        cursor += timedelta(days=7)

    return "\n".join(out)


def _generate_day_slot(d: date, iso: str) -> str:
    """One day's planner section with ruled lines for handwriting."""
    dow = DAY_NAMES[d.weekday()]
    day_num = d.day
    color = "accent" if d.weekday() >= 5 else "ink"

    return "\n".join([
        f"\\textbf{{{dow} {day_num}}} \\moonicon{{{iso}}}{{3mm}} "
        f"\\textcolor{{{color}}}{{\\footnotesize \\moonname{{{iso}}}}}\\par",
        "\\vspace{1mm}",
        "\\noindent\\rule{\\textwidth}{0.2pt}\\\\[4.5mm]",
        "\\noindent\\rule{\\textwidth}{0.2pt}\\\\[4.5mm]",
        "\\noindent\\rule{\\textwidth}{0.2pt}\\\\[4.5mm]",
        "\\noindent\\rule{\\textwidth}{0.2pt}\\\\[4.5mm]",
        "\\noindent\\rule{\\textwidth}{0.2pt}\\\\[4.5mm]",
    ])


def generate_content() -> str:
    """Generate all body content: title page, month grids, week pages."""
    out = []

    # ── Title page ──
    out.extend([
        "\\thispagestyle{empty}",
        "\\vspace*{30mm}",
        "\\begin{center}",
        "{\\fontsize{28}{34}\\textbf{月面日程本}}",
        "\\vspace{6mm}",
        "{\\fontsize{18}{24} 2026}",
        "\\vspace{12mm}",
        "{\\normalsize 静海基地 (Mare Tranquillitatis)}",
        "\\vspace{3mm}",
        "{\\small 环境日志 \\& 个人手帐}",
        "\\vfill",
        "{\\footnotesize senary edition}",
        "\\end{center}",
        "\\clearpage",
        "",
        "% ── Year reference ──",
        "\\thispagestyle{empty}",
        "\\vspace*{30mm}",
        "\\begin{center}",
        "{\\fontsize{20}{26}\\textbf{2026}}",
        "\\vspace{8mm}",
        "{\\normalsize Moon Phase Calendar}",
        "\\vspace{4mm}",
        "{\\small 110×210 mm \\textbullet\\ binding offset 9 mm}",
        "\\vfill",
        "\\end{center}",
        "\\clearpage",
    ])

    # ── Month grids ──
    for m in range(1, 13):
        out.append(f"% ── {MONTH_NAMES[m-1]} ──")
        out.append("\\thispagestyle{plain}")
        out.append(generate_month_grid(YEAR, m))
        out.append("\\clearpage")

    # ── Week pages ──
    out.append("% ── Week pages ──")
    out.append(generate_week_pages())

    return "\n".join(out)


def main():
    data = generate_data_macros()
    data_path = HERE / "moon-data.tex"
    data_path.write_text(data)
    ndays = sum(1 for _ in iter_moon(YEAR))
    print(f"Generated {data_path} ({ndays} days)")

    content = generate_content()
    content_path = HERE / "content.tex"
    content_path.write_text(content)
    npages = content.count("\\clearpage") + 1
    print(f"Generated {content_path} (~{npages} pages)")


if __name__ == "__main__":
    main()
