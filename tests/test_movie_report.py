import unittest
from typing import Any
from unittest import mock

from src.movie_report import movie_report as mr


class FormatDateTests(unittest.TestCase):
    def test_iso_to_mon_dd_yyyy(self) -> None:
        self.assertEqual(mr._format_date("2010-07-15"), "JUL-15-2010")
        self.assertEqual(mr._format_date("2023-10-05"), "OCT-05-2023")

    def test_empty_and_none(self) -> None:
        self.assertEqual(mr._format_date(""), "")
        self.assertEqual(mr._format_date(None), "")

    def test_unparseable_returned_unchanged(self) -> None:
        self.assertEqual(mr._format_date("n/a"), "n/a")

    def test_bad_month_returned_unchanged(self) -> None:
        self.assertEqual(mr._format_date("2010-13-01"), "2010-13-01")


class InitialsTests(unittest.TestCase):
    def test_multi_word(self) -> None:
        self.assertEqual(mr._initials("Breaking Bad"), "BB")
        self.assertEqual(mr._initials("Stranger Things"), "ST")

    def test_single_word(self) -> None:
        self.assertEqual(mr._initials("Inception"), "I")

    def test_cjk_only_falls_back(self) -> None:
        self.assertEqual(mr._initials("盗梦空间"), "XX")

    def test_empty_falls_back(self) -> None:
        self.assertEqual(mr._initials(""), "XX")
        self.assertEqual(mr._initials(None), "XX")


class DossierCodeTests(unittest.TestCase):
    def _report(self, **kw: Any) -> mr.Report:
        defaults: dict[str, Any] = dict(
            kind="tv",
            name="绝命毒师",
            original_name="Breaking Bad",
            date="2008-01-20",
            seasons=(),
        )
        defaults.update(kw)
        return mr.Report(**defaults)

    def test_code_from_original_name(self) -> None:
        self.assertEqual(mr._dossier_code(self._report()), "BB")

    def test_ref_code_prefers_imdb_id(self) -> None:
        self.assertEqual(mr._ref_code(self._report(imdb_id="tt0903747")), "tt0903747")

    def test_ref_code_falls_back_to_initials_year(self) -> None:
        # no imdb_id → INITIALS-YEAR fallback
        self.assertEqual(mr._ref_code(self._report()), "BB-2008")

    def test_ref_code_missing_date(self) -> None:
        self.assertEqual(mr._ref_code(self._report(date="")), "BB-0000")


class StampColsTests(unittest.TestCase):
    def test_a5(self) -> None:
        # 148 mm, margin=10, stamp_w=24 → (148-20)//24 = 5
        self.assertEqual(mr._stamp_cols(148.0, 10.0, 24.0), 5)

    def test_tiny_page_clamps_to_three(self) -> None:
        self.assertEqual(mr._stamp_cols(50.0, 10.0, 24.0), 3)

    def test_huge_page_clamps_to_eight(self) -> None:
        self.assertEqual(mr._stamp_cols(400.0, 10.0, 24.0), 8)

    def test_74m5(self) -> None:
        # 74 mm, margin=8, stamp_w=16 → (74-16)//16 = 3
        self.assertEqual(mr._stamp_cols(74.0, 8.0, 16.0), 3)


class SpreadGridTests(unittest.TestCase):
    def test_partial_row_left_aligned(self) -> None:
        """Fewer items than columns → left-aligned, no stretch."""
        grid = mr._spread_grid(["a", "b", "c"], 10)
        self.assertNotIn(r"\hfil", grid)  # partial row, no spread
        self.assertIn(r"\noindent", grid)
        self.assertEqual(grid.count(r"\noindent"), 1)

    def test_full_rows_spread_evenly(self) -> None:
        """Full rows use \\hfil to spread items across the line width."""
        grid = mr._spread_grid(["a", "b", "c", "d"], 2)
        # 4 items at 2 per row → 2 full rows
        self.assertEqual(grid.count(r"\noindent"), 2)
        self.assertIn(r"\hfil", grid)
        self.assertIn(r"\null", grid)  # anchor at right margin

    def test_wraps_into_rows(self) -> None:
        grid = mr._spread_grid([str(n) for n in range(1, 11)], 4)
        # 10 items at 4 per row → 3 rows (2 full + 1 partial)
        self.assertEqual(grid.count(r"\noindent"), 3)
        # Full rows have \hfil; partial last row does not
        rows = grid.split(r"\par")
        full_rows = [r for r in rows if r.count(r"\hfil")]
        self.assertEqual(len(full_rows), 2)  # first two rows are full

    def test_empty_returns_empty(self) -> None:
        self.assertEqual(mr._spread_grid([], 10), "")

    def test_partial_row_gap_scales(self) -> None:
        """Partial row uses the given gap, not always 4mm."""
        grid = mr._spread_grid(["a", "b", "c"], 10, gap=3.0)
        self.assertIn(r"\hspace{3.0mm}", grid)


class TitleSectionTests(unittest.TestCase):
    def test_has_poster_and_title(self) -> None:
        report = mr.Report("movie", "盗梦空间", "Inception", "2010-07-15", ())
        out = mr._title_section(report)
        self.assertIn(r"\posterbox", out)
        self.assertIn(r"\caplabel{TITLE}", out)
        self.assertIn("盗梦空间", out)
        # the DATE lives in the progress cards, not the title row
        self.assertNotIn(r"\datestamp", out)

    def test_tv_title_has_no_date_stamp(self) -> None:
        # dates live in the cards, not the title row
        report = mr.Report("tv", "show", "Breaking Bad", "2008-01-20", ())
        self.assertNotIn(r"\datestamp", mr._title_section(report))

    def test_shows_original_when_different(self) -> None:
        report = mr.Report("movie", "盗梦空间", "Inception", "2010-07-15", ())
        self.assertIn("Inception", mr._title_section(report))

    def test_hides_original_when_same(self) -> None:
        report = mr.Report("movie", "Inception", "Inception", "2010-07-15", ())
        # original appears only once (inside \MakeUppercase{name}); no subtitle line
        self.assertEqual(mr._title_section(report).count("Inception"), 1)

    def test_placeholder_when_no_poster(self) -> None:
        report = mr.Report("movie", "Inception", "Inception", "2010-07-15", ())
        self.assertIn(r"\posterbox", mr._title_section(report))
        self.assertNotIn(r"\posterimage", mr._title_section(report))

    def test_fetched_poster_when_given(self) -> None:
        report = mr.Report("movie", "Inception", "Inception", "2010-07-15", ())
        out = mr._title_section(report, "poster.jpg")
        self.assertIn(r"\posterimage{poster.jpg}", out)
        self.assertNotIn(r"\posterbox", out)


class DownloadPosterTests(unittest.TestCase):
    def test_writes_file_and_returns_true(self) -> None:
        import io
        import tempfile
        from pathlib import Path

        from PIL import Image

        # A minimal 8×8 red square so the Bayer dither has real pixels to work on.
        img = Image.new("RGB", (8, 8), color=(180, 60, 60))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        valid_jpeg: bytes = buf.getvalue()

        with tempfile.TemporaryDirectory() as tmp:
            dest_path = Path(tmp) / "poster.jpg"
            fake = mock.MagicMock()
            fake.__enter__.return_value.read.return_value = valid_jpeg
            with mock.patch.object(mr.urllib.request, "urlopen", return_value=fake):
                ok = mr._download_poster("/abc.jpg", dest_path)
            self.assertTrue(ok)
            # Output must be a JPEG (starts with FF D8) and non-empty.
            saved = dest_path.read_bytes()
            self.assertTrue(saved[:2] == b"\xff\xd8", "output is not a JPEG")
            self.assertGreater(len(saved), 100)

    def test_returns_false_on_network_error(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            dest_path = Path(tmp) / "poster.jpg"
            with mock.patch.object(
                mr.urllib.request,
                "urlopen",
                side_effect=mr.urllib.error.URLError("boom"),
            ):
                ok = mr._download_poster("/abc.jpg", dest_path)
            self.assertFalse(ok)


class ProgressTests(unittest.TestCase):
    def test_tv_header_says_stamp_episodes(self) -> None:
        report = mr.Report("tv", "show", "Breaking Bad", "2008-01-20", ())
        out = mr._progress_header(report)
        self.assertIn("STAMP EPISODES AS COMPLETED", out)
        self.assertNotIn("PROGRESS LOG", out)

    def test_movie_header_says_mark_completed(self) -> None:
        report = mr.Report("movie", "Inception", "Inception", "2010-07-15", ())
        out = mr._progress_header(report)
        self.assertIn("MARK AS COMPLETED", out)
        self.assertNotIn("PROGRESS LOG", out)

    def test_season_cards_one_per_season(self) -> None:
        seasons = (mr.Season(1, 7, "S1"), mr.Season(2, 3, "S2"))
        report = mr.Report("tv", "show", "Breaking Bad", "2008-01-20", seasons)
        out = mr._season_cards(report, 10)
        self.assertIn(r"\caplabel{SEASON 01}", out)
        self.assertIn(r"\caplabel{SEASON 02}", out)
        self.assertIn(r"\epitem{01}", out)
        self.assertIn(r"\epitem{07}", out)  # last episode of season 1

    def test_season_card_includes_air_date(self) -> None:
        seasons = (
            mr.Season(1, 7, "S1", "2008-01-20"),
            mr.Season(2, 3, "S2", "2009-03-08"),
        )
        report = mr.Report("tv", "show", "Breaking Bad", "2008-01-20", seasons)
        out = mr._season_cards(report, 10)
        self.assertIn(r"\caplabel{AIR DATE}", out)
        self.assertIn(r"\datestamp{JAN-20-2008}", out)
        self.assertIn(r"\datestamp{MAR-08-2009}", out)

    def test_season_card_omits_date_when_missing(self) -> None:
        seasons = (mr.Season(1, 7, "S1"),)  # no air_date
        report = mr.Report("tv", "show", "Breaking Bad", "2008-01-20", seasons)
        out = mr._season_cards(report, 10)
        self.assertNotIn("AIR DATE", out)
        self.assertNotIn(r"\datestamp", out)

    def test_movie_viewing_card(self) -> None:
        report = mr.Report("movie", "Inception", "Inception", "2010-07-15", ())
        out = mr._viewing_card(report, 10)
        self.assertEqual(out.count(r"\seenitem"), mr._VIEWING_SLOTS)
        self.assertNotIn(r"\caplabel{SCREENING}", out)
        # the movie's date sits in the card header, same corner as a TV season
        self.assertIn(r"\caplabel{RELEASE DATE}", out)
        self.assertIn(r"\datestamp{JUL-15-2010}", out)


class BodyTests(unittest.TestCase):
    def _report(self) -> mr.Report:
        return mr.Report("movie", "盗梦空间", "Inception", "2010-07-15", ())

    def test_contains_every_section(self) -> None:
        body = mr._body(self._report(), 7)
        for marker in (
            r"\posterbox",
            r"\datestamp{JUL-15-2010}",
            r"\seenitem",
            r"\perf",
            r"\notesbox",
            r"\reportfooter{I-2010}",
        ):
            self.assertIn(marker, body)


class FetchReportTests(unittest.TestCase):
    def test_movie_mapping(self) -> None:
        payload = {
            "title": "盗梦空间",
            "original_title": "Inception",
            "release_date": "2010-07-15",
            "poster_path": "/xyz.jpg",
            "imdb_id": "tt1375666",
        }
        with mock.patch.object(mr, "_tmdb_get", return_value=payload):
            report = mr.fetch_report("movie", 1, language="zh-CN")
        self.assertEqual(report.kind, "movie")
        self.assertEqual(report.name, "盗梦空间")
        self.assertEqual(report.original_name, "Inception")
        self.assertEqual(report.date, "2010-07-15")
        self.assertEqual(report.seasons, ())
        self.assertEqual(report.poster_path, "/xyz.jpg")
        self.assertEqual(report.imdb_id, "tt1375666")

    def test_tv_seasons_filtered_and_sorted(self) -> None:
        payload = {
            "name": "绝命毒师",
            "original_name": "Breaking Bad",
            "first_air_date": "2008-01-20",
            "poster_path": "/tv.jpg",
            "external_ids": {"imdb_id": "tt0903747"},
            "seasons": [
                {
                    "season_number": 2,
                    "episode_count": 13,
                    "name": "Season 2",
                    "air_date": "2009-03-08",
                },
                {"season_number": 0, "episode_count": 0, "name": "Specials"},
                {
                    "season_number": 1,
                    "episode_count": 7,
                    "name": "Season 1",
                    "air_date": "2008-01-20",
                },
            ],
        }
        with mock.patch.object(mr, "_tmdb_get", return_value=payload):
            report = mr.fetch_report("tv", 2, language="zh-CN")
        self.assertEqual(report.kind, "tv")
        self.assertEqual(report.date, "2008-01-20")
        self.assertEqual(report.poster_path, "/tv.jpg")
        self.assertEqual(report.imdb_id, "tt0903747")
        # 0-episode season dropped; remaining sorted 1, 2
        self.assertEqual([s.number for s in report.seasons], [1, 2])
        self.assertEqual([s.episodes for s in report.seasons], [7, 13])
        self.assertEqual(
            [s.air_date for s in report.seasons], ["2008-01-20", "2009-03-08"]
        )


if __name__ == "__main__":
    unittest.main()
