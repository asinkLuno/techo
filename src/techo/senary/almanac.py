"""LunarAlmanac — the facade that ties the layers together (doc §26, §32–33).

    Astronomy ──┐
    Time ───────┼──▶ LunarAlmanac ──▶ AlmanacDay / JSON
    Partner ────┘

Upper layers never touch the ephemeris engine; they ask the almanac for a
day snapshot.  Batch generation pre-computes a whole month/year so the
typesetting stage stays pure JSON→page (doc §33).
"""

import json
from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path

from .astronomy import (
    LunarAstronomy,
    astronomy_at,
    earth_illumination_trend,
    sun_distance_km,
)
from .bases import LunarBase
from .partners import (
    EarthPartner,
    is_partner_working,
    partner_status,
    partner_time,
)
from .timebase import BJT_TZ, LunationClock, bjt_to_utc, to_bjt, to_utc

# Reference moment for a printed day page: 08:00 LTC (doc §33).
DAY_REFERENCE_LTC = time(8, 0)

# Reference moment for a BJT-anchored day page (doc v2 §Q1): 08:00 BJT =
# 00:00 UTC — the civil morning of the page's BJT date.
DAY_REFERENCE_BJT = time(8, 0)


@dataclass(frozen=True)
class AlmanacDay:
    """Everything one printed page needs (doc §32)."""

    # ── time ──
    utc: datetime  # page reference instant
    date: str  # LTC calendar date, YYYY-MM-DD
    weekday: int  # Monday=0 (Earth-Gregorian admin calendar)

    # ── lunation ──
    lunation_number: int
    lunation_progress: float
    lunation_label: str  # "L094"

    @property
    def lunation_percent(self) -> int:
        """Whole-percent progress for compact display (L094 · 83%)."""
        return round(self.lunation_progress * 100)

    # ── moon sky ──
    astronomy: LunarAstronomy
    earth_trend: str  # "↑" waxing / "↓" waning Earth phase (header arrow)

    # ── earth partner ──
    partner_local_time: datetime
    partner_working: bool
    partner_status_label: str  # "WORK →18:00" / "OFF opens 08:00"
    partner_timezone: str

    # ── metadata ──
    base_id: str
    partner_id: str

    def to_json_dict(self) -> dict:
        """Print-facing dict (doc §33 schema, extended)."""
        astro = self.astronomy
        next_transition, remaining_h = self.next_transition
        return {
            "date": self.date,
            "base": self.base_id,
            "lunation": self.lunation_number,
            "lunation_label": self.lunation_label,
            "lunation_progress": round(self.lunation_progress, 4),
            "solar_altitude": round(astro.solar_altitude_deg, 1),
            "solar_azimuth": round(astro.solar_azimuth_deg, 1),
            "solar_direction": "rising" if astro.solar_trend == "↑" else "falling",
            "lunar_state": (
                "direct-light" if astro.direct_sunlight
                else "shadow" if astro.astronomical_day
                else "night"
            ),
            "astronomical_day": astro.astronomical_day,
            "direct_sunlight": astro.direct_sunlight,
            "next_transition": next_transition,
            "transition_remaining_hours": remaining_h,
            "earth_illumination": round(astro.earth_illumination, 3),
            "earth_trend": "rising" if self.earth_trend == "↑" else "falling",
            "earth_phase": astro.earth_phase_name,
            "earth_altitude": round(astro.earth_altitude_deg, 1),
            "earth_azimuth": round(astro.earth_azimuth_deg, 1),
            "earth_distance_km": round(astro.earth_distance_km),
            "sun_distance_km": round(sun_distance_km(self.utc)),
            "partner_timezone": self.partner_timezone,
            "partner_time": self.partner_local_time.strftime("%H:%M"),
            "partner_working": self.partner_working,
            "partner_status": self.partner_status_label,
        }

    @property
    def next_transition(self) -> tuple[str | None, float | None]:
        """(event label, hours remaining) — polar bases prefer direct light."""
        astro = self.astronomy
        if astro.direct_sunlight:
            event = (astro.next_direct_shadow if astro.next_direct_shadow
                     is not None else astro.next_sunset)
            label = "direct-shadow" if astro.next_direct_shadow is not None else "sunset"
        else:
            event = (astro.next_direct_light if astro.next_direct_light
                     is not None else astro.next_sunrise)
            label = "direct-light" if astro.next_direct_light is not None else "sunrise"
        if event is None:
            return None, None
        return label, (event - self.utc).total_seconds() / 3600.0


class LunarAlmanac:
    """Pre-computable lunar almanac for one (base, partner) pairing."""

    def __init__(self, base: LunarBase, partner: EarthPartner) -> None:
        self.base = base
        self.partner = partner
        self._clock = LunationClock()

    def reference_instant(self, ltc_date: str) -> datetime:
        """08:00 LTC on the given LTC calendar date, as UTC."""
        year, month, day = (int(part) for part in ltc_date.split("-"))
        ltc = datetime(
            year,
            month,
            day,
            DAY_REFERENCE_LTC.hour,
            DAY_REFERENCE_LTC.minute,
            tzinfo=timezone.utc,
        )
        return to_utc(ltc)

    def reference_instant_bjt(self, bjt_date: str) -> datetime:
        """08:00 BJT on the given BJT calendar date, as UTC (day-page axis)."""
        year, month, day = (int(part) for part in bjt_date.split("-"))
        bjt = datetime(
            year,
            month,
            day,
            DAY_REFERENCE_BJT.hour,
            DAY_REFERENCE_BJT.minute,
            tzinfo=BJT_TZ,
        )
        return bjt_to_utc(bjt)

    def at(self, utc: datetime) -> AlmanacDay:
        """Full day snapshot at the given instant."""
        utc = utc.astimezone(timezone.utc)
        # Page calendar identity is the *BJT* civil date (doc v2 open
        # question 1): pre-epoch LTC runs behind UTC by ~0.3 s, which at a
        # midnight reference would roll the LTC date backward — the header
        # must never show yesterday.
        bjt = to_bjt(utc)
        lunation = self._clock.at(utc)
        astro = astronomy_at(self.base, utc)
        local = partner_time(utc, self.partner)
        status = partner_status(utc, self.partner)
        return AlmanacDay(
            utc=utc,
            date=bjt.strftime("%Y-%m-%d"),
            weekday=bjt.weekday(),
            lunation_number=lunation.number,
            lunation_progress=lunation.progress,
            lunation_label=lunation.label,
            astronomy=astro,
            earth_trend=earth_illumination_trend(utc),
            partner_local_time=local,
            partner_working=is_partner_working(local, self.partner),
            partner_status_label=status.label,
            partner_timezone=self.partner.timezone,
            base_id=self.base.id,
            partner_id=self.partner.id,
        )

    def month_days(self, year: int, month: int) -> list[AlmanacDay]:
        """One AlmanacDay per calendar day of the LTC month (08:00 ref)."""
        import calendar as _calendar

        days = _calendar.monthrange(year, month)[1]
        return [
            self.at(self.reference_instant(f"{year:04d}-{month:02d}-{day:02d}"))
            for day in range(1, days + 1)
        ]

    def month_json(self, year: int, month: int) -> str:
        """Batch JSON for a month (doc §33)."""
        days = [d.to_json_dict() for d in self.month_days(year, month)]
        return json.dumps(days, indent=2, ensure_ascii=False)

    def write_month_json(self, year: int, month: int, path: Path) -> None:
        path.write_text(self.month_json(year, month) + "\n", encoding="utf-8")
