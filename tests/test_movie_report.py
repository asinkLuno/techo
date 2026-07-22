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

    def test_ref_code_includes_year(self) -> None:
        self.assertEqual(mr._ref_code(self._report()), "BB-2008")

    def test_ref_code_missing_date(self) -> None:
        self.assertEqual(mr._ref_code(self._report(date="")), "BB-0000")


class StampColsTests(unittest.TestCase):
    def test_a5(self) -> None:
        # 148 mm → (148-20)//18 = 7
        self.assertEqual(mr._stamp_cols(148.0), 7)

    def test_tiny_page_clamps_to_four(self) -> None:
        self.assertEqual(mr._stamp_cols(50.0), 4)

    def test_huge_page_clamps_to_ten(self) -> None:
        self.assertEqual(mr._stamp_cols(400.0), 10)


class SpreadGridTests(unittest.TestCase):
    def test_spreads_with_hfill(self) -> None:
        grid = mr._spread_grid(["a", "b", "c"], 10)
        self.assertIn(r"\hfill", grid)
        self.assertEqual(grid.count(r"\noindent"), 1)

    def test_wraps_into_rows(self) -> None:
        grid = mr._spread_grid([str(n) for n in range(1, 11)], 4)
        # 10 items at 4 per row → 3 rows
        self.assertEqual(grid.count(r"\noindent"), 3)

    def test_empty_returns_empty(self) -> None:
        self.assertEqual(mr._spread_grid([], 10), "")


class TitleSectionTests(unittest.TestCase):
    def test_has_poster_title_and_date_stamp(self) -> None:
        report = mr.Report("movie", "盗梦空间", "Inception", "2010-07-15", ())
        out = mr._title_section(report)
        self.assertIn(r"\posterbox", out)
        self.assertIn(r"\caplabel{TITLE}", out)
        self.assertIn(r"\caplabel{DATE}", out)
        self.assertIn(r"\datestamp{JUL-15-2010}", out)
        self.assertIn("盗梦空间", out)

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
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            dest_path = Path(tmp) / "poster.jpg"
            fake = mock.MagicMock()
            fake.__enter__.return_value.read.return_value = b"\xff\xd8jpeg"
            with mock.patch.object(mr.urllib.request, "urlopen", return_value=fake):
                ok = mr._download_poster("/abc.jpg", dest_path)
            self.assertTrue(ok)
            self.assertEqual(dest_path.read_bytes(), b"\xff\xd8jpeg")

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
        self.assertIn("STAMP EPISODES AS COMPLETED", mr._progress_header(report))

    def test_movie_header_says_mark_completed(self) -> None:
        report = mr.Report("movie", "Inception", "Inception", "2010-07-15", ())
        self.assertIn("MARK AS COMPLETED", mr._progress_header(report))

    def test_season_cards_one_per_season(self) -> None:
        seasons = (mr.Season(1, 7, "S1"), mr.Season(2, 3, "S2"))
        report = mr.Report("tv", "show", "Breaking Bad", "2008-01-20", seasons)
        out = mr._season_cards(report, 10)
        self.assertIn(r"\dossiercard{SEASON 01}", out)
        self.assertIn(r"\dossiercard{SEASON 02}", out)
        self.assertIn(r"\epitem{01}", out)
        self.assertIn(r"\epitem{07}", out)  # last episode of season 1

    def test_movie_screening_card(self) -> None:
        report = mr.Report("movie", "Inception", "Inception", "2010-07-15", ())
        out = mr._screening_card(report, 10)
        self.assertIn(r"\dossiercard{SCREENING}", out)
        self.assertEqual(out.count(r"\stamp{"), mr._MOVIE_STAMPS)


class BodyTests(unittest.TestCase):
    def _report(self) -> mr.Report:
        return mr.Report("movie", "盗梦空间", "Inception", "2010-07-15", ())

    def test_contains_every_section(self) -> None:
        body = mr._body(self._report(), 7)
        for marker in (
            r"\posterbox",
            r"\datestamp{JUL-15-2010}",
            r"\dossiercard{SCREENING}",
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
        }
        with mock.patch.object(mr, "_tmdb_get", return_value=payload):
            report = mr.fetch_report("movie", 1, language="zh-CN")
        self.assertEqual(report.kind, "movie")
        self.assertEqual(report.name, "盗梦空间")
        self.assertEqual(report.original_name, "Inception")
        self.assertEqual(report.date, "2010-07-15")
        self.assertEqual(report.seasons, ())
        self.assertEqual(report.poster_path, "/xyz.jpg")

    def test_tv_seasons_filtered_and_sorted(self) -> None:
        payload = {
            "name": "绝命毒师",
            "original_name": "Breaking Bad",
            "first_air_date": "2008-01-20",
            "poster_path": "/tv.jpg",
            "seasons": [
                {"season_number": 2, "episode_count": 13, "name": "Season 2"},
                {"season_number": 0, "episode_count": 0, "name": "Specials"},
                {"season_number": 1, "episode_count": 7, "name": "Season 1"},
            ],
        }
        with mock.patch.object(mr, "_tmdb_get", return_value=payload):
            report = mr.fetch_report("tv", 2, language="zh-CN")
        self.assertEqual(report.kind, "tv")
        self.assertEqual(report.date, "2008-01-20")
        self.assertEqual(report.poster_path, "/tv.jpg")
        # 0-episode season dropped; remaining sorted 1, 2
        self.assertEqual([s.number for s in report.seasons], [1, 2])
        self.assertEqual([s.episodes for s in report.seasons], [7, 13])


if __name__ == "__main__":
    unittest.main()
