"""Time layer — LTC timescale, BJT civil time, and the Lunation clock.

Three notions of time (design doc §3–4, §10–11):

* **LTC** — Coordinated Lunar Time, the lunar civil timescale.  It is a
  continuous atomic timescale on the lunar reference frame; relativistic
  clock-rate differences versus UTC accumulate ~56.02 µs/day (OSTP 2025
  memo).  The offset is far below print resolution (<0.2 s by 2047) but is
  modelled honestly: LTC = UTC + rate · days_since_epoch.
* **BJT** — Beijing Time, the staff's main civil reference (fixed UTC+8,
  no DST).  Decoupled from the Earth-partner layer: the day page's main
  axis is BJT, with LTC demoted to a secondary column (doc v2 §2).
* **Lunation** — the natural synodic cycle.  Numbered from the official
  epoch L0000 = the lunation containing 2040-01-01 (new moon 2039-12-15
  16:31:45 UTC), computed from actual ephemerides — never the fixed
  29.53059 d mean.  Lunations before the epoch are numbered negatively
  (L-1, L-2, …).  Worked example: 2047-08-16 → L094; 2026-08-01 → L-166.

LTC 管“人什么时候上班”，Lunation 管“太阳现在在哪里”，BJT 管页面主时间轴。
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import ephem

# ── BJT — fixed UTC+8, no DST (staff civil reference, page main axis) ──

BJT_TZ = timezone(timedelta(hours=8), name="BJT")


def to_bjt(utc: datetime) -> datetime:
    """Convert a UTC instant to BJT civil time (fixed +8, no DST)."""
    return utc.astimezone(BJT_TZ)


def bjt_to_utc(bjt: datetime) -> datetime:
    """Convert BJT civil time to UTC."""
    return bjt.astimezone(timezone.utc)


# ── LTC timescale ──

LTC_EPOCH = datetime(2040, 1, 1, tzinfo=timezone.utc)
LTC_RATE_PER_DAY = 56.02e-6  # s/day — relativistic UTC–LTC divergence


def ltc_offset(utc: datetime) -> timedelta:
    """UTC→LTC offset at the given instant (positive: LTC runs ahead)."""
    days = (utc - LTC_EPOCH).total_seconds() / 86400
    return timedelta(seconds=LTC_RATE_PER_DAY * days)


def to_ltc(utc: datetime) -> datetime:
    """Convert UTC to LTC (civil label: UTC + modelled offset)."""
    return utc + ltc_offset(utc)


def to_utc(ltc: datetime) -> datetime:
    """Convert LTC to UTC (inverse of `to_ltc`, exact to sub-µs)."""
    guess = ltc - ltc_offset(ltc)
    return ltc - ltc_offset(guess)


# ── Lunation clock ──

SYNODIC_MONTH_DAYS = 29.53059  # mean, only for scan bounds — never for numbers


def _lunation_containing(target: datetime) -> datetime:
    """New moon opening the lunation that contains *target*.

    The official epoch is the lunation containing 2040-01-01, so L0000
    starts at the new moon of 2039-12-15 — matching the design doc's worked
    example (2047-08-16 → L094).
    """
    nm = ephem.previous_new_moon(target)
    return nm.datetime().replace(tzinfo=timezone.utc)


# Official epoch: L0000 = the lunation containing 2040-01-01.
LUNATION_EPOCH = _lunation_containing(datetime(2040, 1, 1, tzinfo=timezone.utc))
# 2039-12-15 16:31:45 UTC


@dataclass(frozen=True)
class Lunation:
    """Lunation number and progress at one instant (doc §11)."""

    number: int  # 0 = the lunation starting at LUNATION_EPOCH
    progress: float  # 0..1 through the actual (ephemeris) cycle

    @property
    def label(self) -> str:
        """Compact planner label: L094."""
        return f"L{self.number:03d}"


class LunationClock:
    """Ephemeris-backed lunation numbering with a lazy new-moon cache.

    Lunation 0 starts at *epoch* (LUNATION_EPOCH, the lunation containing
    2040-01-01).  Dates before the epoch fall in lunations numbered
    negatively (L-1, L-2, …).  Progress uses the *actual* cycle length
    (previous→next new moon), per the design doc: never a fixed
    29.53059 days.
    """

    def __init__(self, epoch: datetime = LUNATION_EPOCH) -> None:
        self._epoch = epoch
        self._new_moons: list[datetime] = [epoch]
        # prepended pre-epoch moons: self._new_moons[self._offset] == epoch
        self._offset = 0

    def _extend_to(self, utc: datetime) -> None:
        while self._new_moons[-1] <= utc:
            prev = self._new_moons[-1]
            nxt = ephem.next_new_moon(prev).datetime().replace(tzinfo=timezone.utc)
            self._new_moons.append(nxt)

    def _extend_backward_to(self, utc: datetime) -> None:
        while self._new_moons[0] > utc:
            prev = self._new_moons[0]
            nxt = ephem.previous_new_moon(prev).datetime().replace(tzinfo=timezone.utc)
            self._new_moons.insert(0, nxt)
            self._offset += 1

    def _last_new_moon_index(self, utc: datetime) -> int:
        """Index i such that new_moons[i] <= utc < new_moons[i+1]."""
        if utc < self._new_moons[0]:
            self._extend_backward_to(utc)
        else:
            self._extend_to(utc)
        lo, hi = 0, len(self._new_moons) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._new_moons[mid] <= utc:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def at(self, utc: datetime) -> Lunation:
        """Lunation number + progress at *utc* (negative for pre-epoch)."""
        utc = utc.astimezone(timezone.utc)
        i = self._last_new_moon_index(utc)
        start = self._new_moons[i]
        end = self._new_moons[i + 1]
        progress = (utc - start).total_seconds() / (end - start).total_seconds()
        return Lunation(number=i - self._offset, progress=progress)

    def new_moon(self, number: int) -> datetime:
        """UTC instant when the given lunation starts (negative allowed)."""
        while self._offset + number < 0:
            prev = self._new_moons[0]
            nxt = ephem.previous_new_moon(prev).datetime().replace(tzinfo=timezone.utc)
            self._new_moons.insert(0, nxt)
            self._offset += 1
        while len(self._new_moons) - self._offset <= number:
            prev = self._new_moons[-1]
            nxt = ephem.next_new_moon(prev).datetime().replace(tzinfo=timezone.utc)
            self._new_moons.append(nxt)
        return self._new_moons[self._offset + number]
