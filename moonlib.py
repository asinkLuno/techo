"""Shared moon phase calculation utilities.

Used by edition-specific generators (senary, etc.).
"""

import math
import ephem
from datetime import date, timedelta

YEAR = 2026
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def phase_name(phase: float) -> str:
    """Chinese moon phase name from phase [0,1), 0=new."""
    if phase < 0.03 or phase >= 0.97:
        return "新月(朔)"
    if abs(phase - 0.25) < 0.03:
        return "上弦月"
    if abs(phase - 0.5) < 0.03:
        return "满月(望)"
    if abs(phase - 0.75) < 0.03:
        return "下弦月"
    if 0.03 < phase < 0.25:
        return "蛾眉月"
    if 0.25 < phase < 0.5:
        return "盈凸月"
    if 0.5 < phase < 0.75:
        return "亏凸月"
    return "残月"


def iter_moon(year: int):
    """Yield (date, phase, illumination, name) for each day."""
    d = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    while d < end:
        moon = ephem.Moon()
        moon.compute(d.strftime("%Y/%m/%d 12:00"))
        phase = float(moon.moon_phase)  # type: ignore[attr-defined]
        # ponytail: illum from phase — ephem has no .illuminated attr
        illum = (1 - math.cos(2 * math.pi * phase)) / 2
        yield d, phase, illum, phase_name(phase)
        d += timedelta(days=1)


def date_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")
