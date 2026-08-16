"""Astronomy layer — Sun/Earth geometry at a lunar base (doc §12–15, §20–23, §31).

Engine: PyEphem (ELP-based ephemerides).  Conventions verified against
external anchors (see tests/test_almanac.py):

* sub-solar point   = (``subsolar_lat``, 90° − colong), east-longitude
  positive — matched to JPL Horizons DE441/MOON_ME within 0.2°, and to the
  Apollo 11 landing Sun elevation (+10.9° published) within 0.4°.
* sub-Earth point   = (``libration_lat``, ``libration_long``), east-positive —
  pinned by the full-moon coincidence (sub-Earth ≈ sub-solar) to 0.1°.
* Earth phase seen from the Moon is the complement of the lunar phase seen
  from Earth (same Sun–Moon–Earth triangle).

Everything else — alt/az, day/night, terrain-aware direct light, sunrise /
sunset / light transitions — derives from those two zenith points.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import ephem

from .bases import LunarBase
from .timebase import SYNODIC_MONTH_DAYS

_EPOCH_J2000 = ephem.Date("2000/01/01 12:00")

# Transition scan bounds.  Low-latitude bases: the next crossing of a given
# type (sunrise OR sunset) is at most one synodic month away — e.g. just
# after sunset, the next sunset follows a full day/night cycle.  Polar
# bases: the Sun's seasonal altitude cycle runs ~a draconic year, so
# astronomical transitions there may be months away (doc §17, §19) — while
# horizon-profile (direct-light) transitions stay day-scale because the
# azimuth sweeps 360° every lunation.
_SCAN_MAX_DAYS = SYNODIC_MONTH_DAYS + 2.0
_POLAR_SCAN_MAX_DAYS = 346.6 + SYNODIC_MONTH_DAYS
_SCAN_STEP_H = 2.0  # Sun altitude moves ≤1°/h; crossings cannot hide between steps
_POLAR_SCAN_STEP_H = 6.0  # the polar Sun drifts ~0.2°/day


# ── Sub-points ──

def _sub_solar(utc: datetime) -> tuple[float, float]:
    """Sub-solar selenographic point (lat, lon east-positive) in degrees."""
    m = ephem.Moon(utc)
    lat = math.degrees(m.subsolar_lat)
    lon = (90.0 - math.degrees(m.colong) + 180.0) % 360.0 - 180.0
    return lat, lon


def _sub_earth(utc: datetime) -> tuple[float, float]:
    """Sub-Earth selenographic point (lat, lon east-positive) in degrees."""
    m = ephem.Moon(utc)
    return math.degrees(m.libration_lat), math.degrees(m.libration_long)


# ── Local horizon transform ──

def alt_az(
    site_lat: float, site_lon: float, point_lat: float, point_lon: float
) -> tuple[float, float]:
    """Altitude/azimuth (deg) of a sky object whose zenith point is given.

    Azimuth 0°=north, 90°=east, measured from the site to the zenith point
    (a great-circle bearing); exact for the spherical Moon.
    """
    φ, λ, φp, λp = (
        math.radians(site_lat),
        math.radians(site_lon),
        math.radians(point_lat),
        math.radians(point_lon),
    )
    sin_alt = math.sin(φ) * math.sin(φp) + math.cos(φ) * math.cos(φp) * math.cos(λp - λ)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    alt = math.degrees(math.asin(sin_alt))
    cos_alt = math.cos(math.radians(alt))
    if abs(cos_alt) < 1e-9:
        return alt, 0.0  # object at zenith/nadir: azimuth is degenerate
    # initial bearing from site to the zenith point along the great circle
    y = math.sin(λp - λ) * math.cos(φp)
    x = math.cos(φ) * math.sin(φp) - math.sin(φ) * math.cos(φp) * math.cos(λp - λ)
    az = math.degrees(math.atan2(y, x)) % 360.0
    return alt, az


def solar_alt_az(base: LunarBase, utc: datetime) -> tuple[float, float]:
    """Sun altitude/azimuth (deg) at the base."""
    lat, lon = _sub_solar(utc)
    return alt_az(base.latitude_deg, base.longitude_deg, lat, lon)


def earth_alt_az(base: LunarBase, utc: datetime) -> tuple[float, float]:
    """Earth altitude/azimuth (deg) at the base (libration wanders it)."""
    lat, lon = _sub_earth(utc)
    return alt_az(base.latitude_deg, base.longitude_deg, lat, lon)


# ── Illumination & distance ──

def earth_illumination(utc: datetime) -> float:
    """Fraction of the Earth disc lit as seen from the Moon (0..1)."""
    m = ephem.Moon(utc)
    return 1.0 - m.moon_phase


def earth_is_waxing(utc: datetime, sample_h: float = 6.0) -> bool:
    """True if the Earth phase is growing (Moon phase shrinking)."""
    now = earth_illumination(utc)
    later = earth_illumination(utc + timedelta(hours=sample_h))
    earlier = earth_illumination(utc - timedelta(hours=sample_h))
    return later > now or (later == now and now > earlier)


def earth_distance_km(utc: datetime) -> float:
    """Geocentric Earth–Moon distance (km)."""
    return ephem.Moon(utc).earth_distance * 149597870.7


def sun_distance_km(utc: datetime) -> float:
    """Sun–Moon distance (km)."""
    return ephem.Moon(utc).sun_distance * 149597870.7


# ── Phase naming (doc §21) ──

def earth_phase_name(illumination: float, waxing: bool) -> str:
    """Eight-level Earth-phase label, mirroring lunar phase terms."""
    k = illumination
    if k < 0.02:
        return "NEW EARTH"
    if k > 0.98:
        return "FULL EARTH"
    if abs(k - 0.5) < 0.03:
        return "HALF EARTH"
    if k < 0.25:
        return "WAXING CRESCENT" if waxing else "WANING CRESCENT"
    if k < 0.47:
        return "WAXING QUARTER" if waxing else "WANING QUARTER"
    if k < 0.75:
        return "GIBBOUS EARTH"
    return "NEAR FULL" if waxing else "NEAR FULL WANING"


# ── Day / direct light / transitions ──

def solar_altitude(base: LunarBase, utc: datetime) -> float:
    """Sun altitude (deg) above the astronomical horizon."""
    return solar_alt_az(base, utc)[0]


def direct_sunlight(base: LunarBase, utc: datetime) -> bool:
    """True when the Sun clears the *terrain* horizon (doc §17–18)."""
    alt, az = solar_alt_az(base, utc)
    return alt > base.horizon_at(az)


def _sun_excess(base: LunarBase, utc: datetime) -> float:
    """Sun altitude minus terrain horizon (deg); >0 = direct light."""
    alt, az = solar_alt_az(base, utc)
    return alt - base.horizon_at(az)


def next_crossing(
    f,
    t0: datetime,
    increasing: bool,
    max_days: float = _SCAN_MAX_DAYS,
    step_h: float = _SCAN_STEP_H,
) -> datetime | None:
    """First time after *t0* when f crosses 0 in the given direction.

    Bracket scan in *step_h* steps, then bisection to ~10 s.
    """
    t = t0.astimezone(timezone.utc)
    step = timedelta(hours=step_h)
    limit = t + timedelta(days=max_days)
    prev_v = f(t)
    while t < limit:
        nxt = min(t + step, limit)
        v = f(nxt)
        crossed_up = increasing and prev_v <= 0.0 < v
        crossed_down = (not increasing) and prev_v >= 0.0 > v
        if crossed_up or crossed_down:
            lo, hi = t, nxt
            for _ in range(40):  # bisect to sub-second
                mid = lo + (hi - lo) / 2
                mid_v = f(mid)
                crossed_mid_up = increasing and mid_v <= 0.0
                crossed_mid_down = (not increasing) and mid_v >= 0.0
                if crossed_mid_up or crossed_mid_down:
                    lo = mid
                else:
                    hi = mid
            return hi
        t, prev_v = nxt, v
    return None


def _scan_params(base: LunarBase) -> tuple[float, float]:
    """(max_days, step_hours) for this base's astronomical scans."""
    if base.is_polar:
        return _POLAR_SCAN_MAX_DAYS, _POLAR_SCAN_STEP_H
    return _SCAN_MAX_DAYS, _SCAN_STEP_H


def next_sunrise(base: LunarBase, utc: datetime) -> datetime | None:
    """Next time the Sun crosses above the astronomical horizon."""
    bound, step = _scan_params(base)
    return next_crossing(
        lambda t: solar_altitude(base, t), utc, increasing=True,
        max_days=bound, step_h=step,
    )


def next_sunset(base: LunarBase, utc: datetime) -> datetime | None:
    """Next time the Sun crosses below the astronomical horizon."""
    bound, step = _scan_params(base)
    return next_crossing(
        lambda t: solar_altitude(base, t), utc, increasing=False,
        max_days=bound, step_h=step,
    )


def next_direct_light(base: LunarBase, utc: datetime) -> datetime | None:
    """Next time the Sun clears the terrain horizon (shadow → light)."""
    return next_crossing(lambda t: _sun_excess(base, t), utc, increasing=True)


def next_direct_shadow(base: LunarBase, utc: datetime) -> datetime | None:
    """Next time the Sun sinks behind the terrain (light → shadow)."""
    return next_crossing(lambda t: _sun_excess(base, t), utc, increasing=False)


def solar_trend(base: LunarBase, utc: datetime) -> str:
    """'↑' rising or '↓' falling Sun, sampled ±3 h (doc §13)."""
    now = solar_altitude(base, utc)
    later = solar_altitude(base, utc + timedelta(hours=3))
    return "↑" if later > now else "↓"


@dataclass(frozen=True)
class LunarAstronomy:
    """Bundle of sky facts for one base & instant (doc §31)."""

    solar_altitude_deg: float
    solar_azimuth_deg: float
    solar_trend: str  # "↑" / "↓"
    astronomical_day: bool
    direct_sunlight: bool

    next_sunrise: datetime | None
    next_sunset: datetime | None
    next_direct_light: datetime | None
    next_direct_shadow: datetime | None

    earth_altitude_deg: float
    earth_azimuth_deg: float
    earth_illumination: float
    earth_phase_name: str
    earth_distance_km: float


def astronomy_at(base: LunarBase, utc: datetime) -> LunarAstronomy:
    """Compute the full astronomy bundle for *base* at *utc*."""
    utc = utc.astimezone(timezone.utc)
    sun_alt, sun_az = solar_alt_az(base, utc)
    earth_alt, earth_az = earth_alt_az(base, utc)
    illum = earth_illumination(utc)
    waxing = earth_is_waxing(utc)
    light = direct_sunlight(base, utc)
    return LunarAstronomy(
        solar_altitude_deg=sun_alt,
        solar_azimuth_deg=sun_az,
        solar_trend=solar_trend(base, utc),
        astronomical_day=sun_alt > 0.0,
        direct_sunlight=light,
        next_sunrise=next_sunrise(base, utc),
        next_sunset=next_sunset(base, utc),
        next_direct_light=next_direct_light(base, utc) if base.horizon_profile else None,
        next_direct_shadow=next_direct_shadow(base, utc) if base.horizon_profile else None,
        earth_altitude_deg=earth_alt,
        earth_azimuth_deg=earth_az,
        earth_illumination=illum,
        earth_phase_name=earth_phase_name(illum, waxing),
        earth_distance_km=earth_distance_km(utc),
    )
