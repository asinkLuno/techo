"""Base & horizon layers — lunar bases and their local terrain (doc §17–19, §27).

A base is a selenographic site: latitude, longitude, altitude, and optionally
a 360° horizon profile (terrain elevation versus azimuth).  Low-latitude
bases (Tranquillity) need no profile — the astronomical horizon suffices.
Polar bases (Shackleton) live in shadowed crater country, where ridge lines
hide a Sun that is astronomically above the horizon; for those the profile
decides **direct sunlight** versus astronomical day.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HorizonProfile:
    """Terrain horizon heights sampled by azimuth (doc §18).

    Samples are (azimuth_deg, horizon_elevation_deg) pairs; azimuth 0=north,
    90=east.  Lookup interpolates linearly between neighbours and wraps
    across the 0°/360° seam.  The stock profile below is a plausible
    illustrative ridge (replace with LOLA-derived data for production).
    """

    samples: tuple[tuple[float, float], ...] = field(default_factory=tuple)

    @classmethod
    def from_pairs(cls, pairs: list[tuple[float, float]]) -> "HorizonProfile":
        normed = sorted((az % 360.0, el) for az, el in pairs)
        return cls(samples=tuple(normed))

    def at(self, azimuth_deg: float) -> float:
        """Terrain elevation (deg) in the given azimuth direction."""
        if not self.samples:
            return 0.0
        az = azimuth_deg % 360.0
        first_az, first_el = self.samples[0]
        if len(self.samples) == 1 or az <= first_az:
            # interpolate across the wrap seam with the last sample
            last_az, last_el = self.samples[-1]
            prev_az, prev_el = last_az - 360.0, last_el
            next_az, next_el = first_az, first_el
        else:
            lo, hi = 0, len(self.samples) - 1
            while lo < hi - 1:
                mid = (lo + hi) // 2
                if self.samples[mid][0] <= az:
                    lo = mid
                else:
                    hi = mid
            prev_az, prev_el = self.samples[lo]
            next_az, next_el = self.samples[hi]
        if next_az == prev_az:
            return prev_el
        t = (az - prev_az) / (next_az - prev_az)
        return prev_el + t * (next_el - prev_el)


@dataclass(frozen=True)
class LunarBase:
    """A selenographic site the almanac is computed for (doc §27)."""

    id: str
    name: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float = 0.0
    horizon_profile: HorizonProfile | None = None

    def horizon_at(self, azimuth_deg: float) -> float:
        """Terrain elevation toward *azimuth*; 0 without a profile."""
        if self.horizon_profile is None:
            return 0.0
        return self.horizon_profile.at(azimuth_deg)

    @property
    def is_polar(self) -> bool:
        """Polar bases distinguish direct light from astronomical day."""
        return abs(self.latitude_deg) >= 85.0


# ── Stock bases ──
# Tranquillity Base — Apollo 11 site, Mare Tranquillitatis (doc §16, §27).
TRANQUILLITY = LunarBase(
    id="tranquillity",
    name="Tranquillity Base",
    latitude_deg=0.674,
    longitude_deg=23.473,
    altitude_m=0.0,
    horizon_profile=None,
)

# Shackleton Base — lunar south pole rim country (doc §17–19).  The horizon
# profile is an illustrative ridge: the broad envelope (high ridge toward the
# north / Malapert massif, low spill toward the south) plus fine-scale crater-rim
# crests every ~9° of azimuth, so direct sunlight switches on and off several
# times a day as the Sun's azimuth sweeps (doc v2 §4).  Swap in LOLA-derived
# terrain data for production.

def _shackleton_profile() -> HorizonProfile:
    """Envelope (30° skeleton) + 9°-period ripple, sampled every 4°."""
    import math

    skeleton = [
        (0.0, 2.6),
        (30.0, 2.2),
        (60.0, 1.4),
        (90.0, 0.8),
        (120.0, 0.6),
        (150.0, 0.5),
        (180.0, 0.6),
        (210.0, 0.8),
        (240.0, 1.1),
        (270.0, 1.6),
        (300.0, 2.2),
        (330.0, 2.5),
        (360.0, 2.6),
    ]

    def envelope(az: float) -> float:
        for (a0, e0), (a1, e1) in zip(skeleton, skeleton[1:]):
            if a0 <= az <= a1:
                return e0 + (e1 - e0) * (az - a0) / (a1 - a0)
        return skeleton[0][1]

    ripple_amp = 0.55  # °, ridge crests ≈ sun altitude during polar summer
    ripple_period = 9.0  # ° of azimuth — several crests per day's ~12° sweep
    ripple_phase = 20.0  # ° — keep 0°/360° south-of-north consistent
    pairs = []
    for az in range(0, 360, 4):
        ripple = ripple_amp * math.sin((az - ripple_phase) * 2 * math.pi / ripple_period)
        pairs.append((float(az), round(envelope(az) + ripple, 3)))
    return HorizonProfile.from_pairs(pairs)


SHACKLETON = LunarBase(
    id="shackleton",
    name="Shackleton Base",
    latitude_deg=-89.67,
    longitude_deg=0.09,
    altitude_m=0.0,
    horizon_profile=_shackleton_profile(),
)

BASES: dict[str, LunarBase] = {b.id: b for b in (TRANQUILLITY, SHACKLETON)}


def base_by_id(name: str) -> LunarBase:
    """Look up a base by id with a useful domain error."""
    try:
        return BASES[name]
    except KeyError as error:
        known = ", ".join(BASES)
        raise ValueError(f"unknown base {name!r}; known bases: {known}") from error
