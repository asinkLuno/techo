"""Partner layer — Earth Partner time and work windows (doc §5–9, §28–30).

Each lunar worker belongs to an Earth organisation (“Earth Partner”) that
relays mail, meetings and admin.  What the worker really needs is not UTC
but “is my partner in the office?” — so the almanac carries the partner's
IANA local time (DST handled automatically; never hard-coded offsets) and
its scheduled work window.

`WORK WINDOW` means *scheduled office hours*, not a live network status —
the whole almanac stays pre-computable for print.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class EarthPartner:
    """An Earth organisation behind a lunar worker (doc §28)."""

    id: str
    name: str
    timezone: str  # IANA name — DST resolves itself
    work_start: time
    work_end: time
    short: str  # planner label, e.g. "BEIJING"

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


# ── Stock partners (doc §6.1) ──
CNSA = EarthPartner(
    id="cnsa",
    name="CNSA · Beijing Lunar Research Center",
    timezone="Asia/Shanghai",
    work_start=time(9, 0),
    work_end=time(18, 0),
    short="BEIJING",
)
HOUSTON = EarthPartner(
    id="houston",
    name="NASA · Houston Mission Control",
    timezone="America/Chicago",
    work_start=time(8, 0),
    work_end=time(17, 0),
    short="HOUSTON",
)
ESA = EarthPartner(
    id="esa",
    name="ESA · Darmstadt Operations",
    timezone="Europe/Berlin",
    work_start=time(9, 0),
    work_end=time(18, 0),
    short="DARMSTADT",
)

PARTNERS: dict[str, EarthPartner] = {p.id: p for p in (CNSA, HOUSTON, ESA)}


def partner_by_id(name: str) -> EarthPartner:
    """Look up a partner by id with a useful domain error."""
    try:
        return PARTNERS[name]
    except KeyError as error:
        known = ", ".join(PARTNERS)
        raise ValueError(f"unknown partner {name!r}; known partners: {known}") from error


def partner_time(utc: datetime, partner: EarthPartner) -> datetime:
    """Partner local time for a UTC instant (doc §29)."""
    return utc.astimezone(partner.tz)


def is_partner_working(local: datetime, partner: EarthPartner) -> bool:
    """True inside the scheduled work window (doc §30, start inclusive)."""
    return partner.work_start <= local.time() < partner.work_end


@dataclass(frozen=True)
class PartnerStatus:
    """Work-window status at one instant, for the page header (doc §24)."""

    working: bool
    label: str  # "WORK →18:00" or "OFF opens 08:00"


def partner_status(utc: datetime, partner: EarthPartner) -> PartnerStatus:
    """Status line for the partner at *utc*."""
    local = partner_time(utc, partner)
    if is_partner_working(local, partner):
        label = f"WORK →{partner.work_end.strftime('%H:%M')}"
        return PartnerStatus(True, label)
    nxt, _ = _next_window_start(utc, partner)
    opens = partner_time(nxt, partner).strftime("%H:%M")
    return PartnerStatus(False, f"OFF opens {opens}")


def _local_date_window(local_date: date, partner: EarthPartner) -> tuple[datetime, datetime]:
    """Work window [start, end) as UTC instants for one partner-local date."""
    tz = partner.tz

    def at(t: time, day: date) -> datetime:
        naive = datetime.combine(day, t)
        return naive.replace(tzinfo=tz).astimezone(timezone.utc)

    if partner.work_start <= partner.work_end:  # same-day window
        return at(partner.work_start, local_date), at(partner.work_end, local_date)
    # overnight window: start today, end tomorrow
    return at(partner.work_start, local_date), at(partner.work_end, local_date + timedelta(days=1))


def work_window_segments(
    day_start_utc: datetime, duration: timedelta, partner: EarthPartner
) -> list[tuple[datetime, datetime]]:
    """UTC work-window segments overlapping [day_start, day_start+duration).

    Handles DST shifts and windows that straddle lunar midnight; each
    partner-local calendar day contributes one segment.
    """
    day_end = day_start_utc + duration
    segments: list[tuple[datetime, datetime]] = []
    first_local = partner_time(day_start_utc, partner).date()
    last_local = partner_time(day_end, partner).date()
    local_day = first_local
    while local_day <= last_local:
        seg_start, seg_end = _local_date_window(local_day, partner)
        lo, hi = max(seg_start, day_start_utc), min(seg_end, day_end)
        if lo < hi:
            segments.append((lo, hi))
        local_day += timedelta(days=1)
    return sorted(segments)


def _next_window_start(utc: datetime, partner: EarthPartner) -> tuple[datetime, date]:
    """Next work-window opening at/after *utc* (UTC instant + local date)."""
    local = partner_time(utc, partner)
    for offset in range(3):
        day = local.date() + timedelta(days=offset)
        seg_start, seg_end = _local_date_window(day, partner)
        if utc < seg_start:
            return seg_start, day
        if seg_start <= utc < seg_end:
            return seg_start, day
    raise RuntimeError("work window not found within three days")  # pragma: no cover
