"""Anchors for the lunar-almanac astronomy layer.

Every number here is checked against an independent authority:

* Apollo 11 landing (1969-07-20 20:17:40 UTC): published Sun elevation at
  Tranquillity Base ≈ +10.9° (Apollo 11 Mission Report).
* JPL Horizons DE441/MOON_ME: sub-solar point at 2047-08-16 08:42 UTC is
  (lat −0.972°, lon 236.818°E ≡ −123.182°); sub-Earth point is pinned by
  the full-moon coincidence (sub-Earth ≈ sub-solar when Sun and Earth
  align behind the Moon).
* Design doc §10–11: L0000 = the lunation containing 2040-01-01, and the
  worked example 2047-08-16 → L094.
"""

import unittest
from datetime import datetime, timedelta, timezone

import ephem

from techo.senary.almanac import LunarAlmanac
from techo.senary.astronomy import (
    earth_illumination,
    earth_is_waxing,
    next_sunrise,
    next_sunset,
    solar_alt_az,
    solar_altitude,
)
from techo.senary.bases import SHACKLETON, TRANQUILLITY
from techo.senary.partners import CNSA, HOUSTON, is_partner_working, partner_time
from techo.senary.timebase import (
    LUNATION_EPOCH,
    LunationClock,
    ltc_offset,
    to_ltc,
    to_utc,
)

UTC = timezone.utc


def utc(*parts) -> datetime:
    return datetime(*parts, tzinfo=UTC)


class SelenographicGeometryTests(unittest.TestCase):
    """Sub-points and alt/az against JPL Horizons and Apollo 11."""

    def test_apollo11_sun_elevation_at_tranquillity(self) -> None:
        landing = utc(1969, 7, 20, 20, 17, 40)
        alt, _ = solar_alt_az(TRANQUILLITY, landing)
        self.assertAlmostEqual(alt, 10.9, delta=0.6)  # published 10.9°

    def test_subsolar_point_matches_horizons(self) -> None:
        # JPL Horizons DE441/MOON_ME at 2047-08-16 08:42 UTC:
        # SunSub-LAT −0.972°, SunSub-LON 236.818°E (≡ −123.182° east).
        from techo.senary.astronomy import _sub_solar

        lat, lon = _sub_solar(utc(2047, 8, 16, 8, 42))
        self.assertAlmostEqual(lat, -0.972, delta=0.3)
        self.assertAlmostEqual((lon - (-123.182) + 180) % 360 - 180, 0.0, delta=0.3)

    def test_subsolar_longitude_is_90_minus_colong(self) -> None:
        m = ephem.Moon("2047-08-16 08:42")
        expected = (90.0 - float(m.colong) * 180.0 / 3.141592653589793 + 180.0) % 360 - 180
        from techo.senary.astronomy import _sub_solar

        _, lon = _sub_solar(utc(2047, 8, 16, 8, 42))
        self.assertAlmostEqual((lon - expected + 180) % 360 - 180, 0.0, delta=1e-6)

    def test_subearth_aligns_with_subsolar_at_full_moon(self) -> None:
        # At an exact full moon the Sun and Earth lie on the same line as
        # seen from the Moon → sub-Earth ≈ sub-solar (within lunar-orbit
        # tilt, a few degrees).
        from techo.senary.astronomy import _sub_earth, _sub_solar

        for t in ("2039-12-30 12:37:27", "2047-08-05 20:38:00"):
            se = ephem.next_full_moon(t)
            e_lat, e_lon = _sub_earth(se.datetime().replace(tzinfo=UTC))
            s_lat, s_lon = _sub_solar(se.datetime().replace(tzinfo=UTC))
            self.assertAlmostEqual(
                _sep(e_lat, e_lon, s_lat, s_lon), 0.0, delta=6.0
            )

    def test_subearth_antipodal_at_new_moon(self) -> None:
        from techo.senary.astronomy import _sub_earth, _sub_solar

        nm = ephem.next_new_moon("2040-01-01")
        e_lat, e_lon = _sub_earth(nm.datetime().replace(tzinfo=UTC))
        s_lat, s_lon = _sub_solar(nm.datetime().replace(tzinfo=UTC))
        self.assertAlmostEqual(_sep(e_lat, e_lon, s_lat, s_lon), 180.0, delta=6.0)

    def test_earth_altitude_at_tranquillity_is_high(self) -> None:
        # Tranquillity Base is a low-latitude near-side site; Earth rides
        # high in its sky (sub-Earth wanders only ±8°).
        from techo.senary.astronomy import earth_alt_az

        alt, _ = earth_alt_az(TRANQUILLITY, utc(2047, 8, 16, 8, 42))
        self.assertGreater(alt, 55.0)
        self.assertLess(alt, 90.0)

    def test_earth_illumination_is_moon_phase_complement(self) -> None:
        m = ephem.Moon("2047-08-16 08:42")
        self.assertAlmostEqual(earth_illumination(utc(2047, 8, 16, 8, 42)), 1 - m.moon_phase, delta=1e-6)

    def test_earth_waxing_matches_moon_waning(self) -> None:
        # Earth phase grows while the lunar phase shrinks.
        m1 = ephem.Moon("2047-08-16 08:42")
        m2 = ephem.Moon("2047-08-16 14:42")
        waxing = earth_is_waxing(utc(2047, 8, 16, 8, 42))
        self.assertEqual(waxing, m2.moon_phase < m1.moon_phase)


def _sep(lat1, lon1, lat2, lon2) -> float:
    """Angular separation (deg) of two selenographic points."""
    import math

    a, b, c, d = map(math.radians, (lat1, lon1, lat2, lon2))
    return math.degrees(
        math.acos(
            max(
                -1,
                min(
                    1,
                    math.sin(a) * math.sin(c)
                    + math.cos(a) * math.cos(c) * math.cos(d - b),
                ),
            )
        )
    )


class LunationTests(unittest.TestCase):
    def test_epoch_is_lunation_containing_2040_01_01(self) -> None:
        self.assertEqual(LUNATION_EPOCH.date().isoformat(), "2039-12-15")

    def test_worked_example_2047_08_16_is_L094(self) -> None:
        clock = LunationClock()
        lunation = clock.at(utc(2047, 8, 16, 8, 42))
        self.assertEqual(lunation.number, 94)
        self.assertEqual(lunation.label, "L094")
        self.assertAlmostEqual(lunation.progress, 0.83, delta=0.02)

    def test_progress_uses_actual_cycle_not_mean(self) -> None:
        # Progress must come from real ephemeris new moons, not 29.53059.
        clock = LunationClock()
        l1 = clock.at(utc(2047, 8, 16, 8, 42))
        start = clock.new_moon(94)
        end = clock.new_moon(95)
        expected = (utc(2047, 8, 16, 8, 42) - start) / (end - start)
        self.assertAlmostEqual(l1.progress, expected, places=9)

    def test_numbering_monotonic_and_consecutive(self) -> None:
        clock = LunationClock()
        nm = clock.new_moon(94)  # exact 2047-07-22 22:48:50.98
        a = clock.at(nm)
        b = clock.at(nm + timedelta(hours=1))
        self.assertEqual(a.number, 94)
        self.assertAlmostEqual(a.progress, 0.0, delta=1e-9)
        self.assertEqual(b.number, 94)
        self.assertAlmostEqual(b.progress, 0.0014, delta=0.001)


class LTCTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        t = utc(2047, 8, 16, 8, 42)
        self.assertAlmostEqual(to_utc(to_ltc(t)), t, delta=utc(2000, 1, 1) - utc(1999, 12, 31, 23, 59, 59))

    def test_offset_magnitude_at_2047(self) -> None:
        # ~56 µs/day × ~7.6 years ≈ 0.15 s — below print resolution but modelled.
        offset = ltc_offset(utc(2047, 8, 16))
        self.assertGreater(offset.total_seconds(), 0.1)
        self.assertLess(offset.total_seconds(), 0.2)


class PartnerTests(unittest.TestCase):
    def test_beijing_is_utc_plus_8(self) -> None:
        self.assertEqual(partner_time(utc(2047, 8, 16, 0, 30), CNSA).hour, 8)
        self.assertEqual(partner_time(utc(2047, 8, 16, 8, 42), CNSA).strftime("%H:%M"), "16:42")

    def test_houston_dst_handled_automatically(self) -> None:
        summer = partner_time(utc(2047, 8, 16, 12), HOUSTON)  # CDT = UTC−5
        winter = partner_time(utc(2047, 1, 15, 12), HOUSTON)  # CST = UTC−6
        self.assertEqual(summer.hour, 7)
        self.assertEqual(winter.hour, 6)

    def test_work_window(self) -> None:
        self.assertTrue(is_partner_working(partner_time(utc(2047, 8, 16, 1, 0), CNSA), CNSA))  # 09:00 BJT
        self.assertFalse(is_partner_working(partner_time(utc(2047, 8, 16, 10, 0), CNSA), CNSA))  # 18:00 BJT

    def test_window_segments_cover_full_day(self) -> None:
        from datetime import timedelta

        from techo.senary.partners import work_window_segments

        t0 = utc(2047, 8, 16, 0, 0)
        segs = work_window_segments(t0, timedelta(hours=24), CNSA)
        # Beijing 09:00–18:00 = UTC 01:00–10:00, one segment inside this day
        self.assertEqual(len(segs), 1)
        start, end = segs[0]
        self.assertEqual(start.hour, 1)
        self.assertEqual(end.hour, 10)


class BaseTests(unittest.TestCase):
    def test_shackleton_astronomical_day_but_no_direct_light(self) -> None:
        # 2047-08-16: Sun +0.8° astronomically up, but the north ridge
        # (horizon ≈ +1.1° at az 236°) blocks it.
        t = utc(2047, 8, 16, 8, 42)
        alt = solar_altitude(SHACKLETON, t)
        self.assertGreater(alt, 0.0)
        from techo.senary.astronomy import direct_sunlight

        self.assertFalse(direct_sunlight(SHACKLETON, t))

    def test_horizon_profile_wraps_azimuth(self) -> None:
        profile = SHACKLETON.horizon_profile
        assert profile is not None
        # 359° interpolates between 330° and 0° across the seam
        self.assertAlmostEqual(profile.at(359.0), profile.at(1.0), delta=2.0)
        self.assertAlmostEqual(profile.at(0.0), 2.6, delta=0.01)

    def test_tranquillity_sunrise_sunset_span_half_lunation(self) -> None:
        t = utc(2047, 8, 16, 8, 42)
        sunrise = next_sunrise(TRANQUILLITY, t)
        sunset = next_sunset(TRANQUILLITY, t)
        assert sunrise is not None and sunset is not None
        span = (sunset - sunrise).total_seconds() / 86400
        self.assertAlmostEqual(span, 14.77, delta=1.0)


class AlmanacFacadeTests(unittest.TestCase):
    def test_day_snapshot_shape(self) -> None:
        day = LunarAlmanac(TRANQUILLITY, CNSA).at(utc(2047, 8, 16, 8, 42))
        self.assertEqual(day.date, "2047-08-16")
        self.assertEqual(day.lunation_label, "L094")
        self.assertFalse(day.astronomy.astronomical_day)
        self.assertTrue(day.partner_working)  # 16:42 BJT
        self.assertEqual(day.partner_timezone, "Asia/Shanghai")

    def test_json_schema_matches_doc(self) -> None:
        day = LunarAlmanac(TRANQUILLITY, CNSA).at(utc(2047, 8, 16, 8, 42))
        data = day.to_json_dict()
        for key in (
            "date",
            "base",
            "lunation",
            "lunation_progress",
            "solar_altitude",
            "solar_direction",
            "lunar_state",
            "next_transition",
            "transition_remaining_hours",
            "earth_illumination",
            "earth_altitude",
            "partner_timezone",
            "partner_time",
            "partner_working",
        ):
            self.assertIn(key, data)
        self.assertEqual(data["lunation"], 94)
        self.assertEqual(data["next_transition"], "sunrise")

    def test_month_json_is_a_list(self) -> None:
        import json

        payload = LunarAlmanac(TRANQUILLITY, CNSA).month_json(2047, 8)
        self.assertEqual(len(json.loads(payload)), 31)


if __name__ == "__main__":
    unittest.main()
