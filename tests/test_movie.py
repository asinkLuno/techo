import unittest
from unittest import mock

from src.movie import movie


class TexEscapeTests(unittest.TestCase):
    def test_escapes_special_characters(self) -> None:
        escaped = movie._tex_escape("a & b% c#d_e $f {g} h~i^j")
        for token in (
            r"\&",
            r"\%",
            r"\#",
            r"\_",
            r"\$",
            r"\{",
            r"\}",
            r"\textasciitilde{}",
            r"\textasciicircum{}",
        ):
            self.assertIn(token, escaped)

    def test_escapes_backslash(self) -> None:
        self.assertIn(r"\textbackslash{}", movie._tex_escape("a\\b"))

    def test_empty(self) -> None:
        self.assertEqual(movie._tex_escape(""), "")
        self.assertEqual(movie._tex_escape(None), "")


class SlugTests(unittest.TestCase):
    def test_lowercases_and_dashes(self) -> None:
        self.assertEqual(movie._slug("Inception"), "inception")

    def test_keeps_cjk(self) -> None:
        self.assertEqual(movie._slug("盗梦空间"), "盗梦空间")

    def test_replaces_punctuation(self) -> None:
        self.assertEqual(movie._slug("A/B: C"), "a-b-c")

    def test_empty_fallback(self) -> None:
        self.assertEqual(movie._slug(""), "untitled")
        self.assertEqual(movie._slug("   "), "untitled")


class ColsThatFitTests(unittest.TestCase):
    def test_floors_to_whole_columns(self) -> None:
        self.assertEqual(movie._cols_that_fit(57.0, 5.0), 11)
        self.assertEqual(movie._cols_that_fit(4.9, 5.0), 1)

    def test_tiny_width_still_one(self) -> None:
        self.assertEqual(movie._cols_that_fit(1.0, 5.0), 1)


class CellsTests(unittest.TestCase):
    def test_four_edges_per_cell(self) -> None:
        # each cell draws top, bottom, left, right -> 4 draws (shared edges doubled)
        lines = movie._cells(0.0, 0.0, count=5, cols=11, cell=5.0)
        self.assertEqual(len([ln for ln in lines if "\\draw" in ln]), 4 * 5)

    def test_ragged_last_row_is_exact(self) -> None:
        # 13 episodes at 11 cols -> two rows; exactly 13 cells (no padding)
        lines = movie._cells(0.0, 0.0, count=13, cols=11, cell=5.0)
        self.assertEqual(len([ln for ln in lines if "\\draw" in ln]), 4 * 13)


class GridDrawingTests(unittest.TestCase):
    def test_cell_numbers_one_per_number(self) -> None:
        nodes = movie._cell_numbers(
            0.0, 0.0, cols=4, cell=5.0, numbers=list(range(1, 11)), font="FontSmall"
        )
        self.assertEqual(len(nodes), 10)
        self.assertTrue(all("\\node" in ln for ln in nodes))
        self.assertIn("{1}", nodes[0])
        self.assertIn("{10}", nodes[-1])

    def test_stars_count(self) -> None:
        self.assertEqual(len(movie._stars(37.0, 80.0)), 5)


class PackSeasonsTests(unittest.TestCase):
    def test_many_small_seasons_pack_onto_few_pages(self) -> None:
        seasons = tuple(movie.Season(n, 7, f"S{n}") for n in range(1, 4))
        pages = movie._pack_seasons(seasons, "74m5", 74.0, 105.0)
        self.assertEqual(len(pages), 1)  # three 1-row seasons fit on one page

    def test_overflow_creates_more_pages(self) -> None:
        seasons = tuple(movie.Season(n, 13, f"S{n}") for n in range(1, 21))
        pages = movie._pack_seasons(seasons, "74m5", 74.0, 105.0)
        self.assertGreater(len(pages), 1)

    def test_numbers_present_per_season(self) -> None:
        seasons = (movie.Season(1, 7, "S1"), movie.Season(2, 3, "S2"))
        pages = movie._pack_seasons(seasons, "74m5", 74.0, 105.0)
        joined = "\n".join("\n".join(p) for p in pages)
        self.assertIn("{7}", joined)  # last ep of season 1
        self.assertIn("S01", joined)
        self.assertIn("S02", joined)

    def test_preserves_given_season_order(self) -> None:
        # sorting (specials last) is fetch_title's job; _pack_seasons keeps given order
        seasons = (movie.Season(1, 7, "S1"), movie.Season(0, 3, "Specials"))
        pages = movie._pack_seasons(seasons, "74m5", 74.0, 105.0)
        joined = "\n".join("\n".join(p) for p in pages)
        self.assertIn("S00", joined)
        self.assertLess(joined.index("S01"), joined.index("S00"))


class MarginsTests(unittest.TestCase):
    def test_known_size_keys(self) -> None:
        # 74m5 is defined in GREEN_DOT; locks the (binding, right, top, bottom) tuple.
        self.assertEqual(movie._margins("74m5"), (12, 5, 10, 10))

    def test_unknown_size_falls_back(self) -> None:
        binding, right, top, bottom = movie._margins("does-not-exist")
        self.assertEqual((binding, right, top, bottom), (12, 5, 10, 10))


class ResultSummaryTests(unittest.TestCase):
    def test_movie(self) -> None:
        kind, name, original, year = movie._result_summary(
            {
                "media_type": "movie",
                "title": "盗梦空间",
                "original_title": "Inception",
                "release_date": "2010-07-15",
            }
        )
        self.assertEqual((kind, name, original, year), ("movie", "盗梦空间", "Inception", "2010"))

    def test_tv(self) -> None:
        kind, name, original, year = movie._result_summary(
            {
                "media_type": "tv",
                "name": "绝命毒师",
                "original_name": "Breaking Bad",
                "first_air_date": "2008-01-20",
            }
        )
        self.assertEqual((kind, name, original, year), ("tv", "绝命毒师", "Breaking Bad", "2008"))

    def test_person_has_no_year(self) -> None:
        kind, _, _, year = movie._result_summary(
            {"media_type": "person", "name": "Christopher Nolan"}
        )
        self.assertEqual(kind, "person")
        self.assertEqual(year, "")


def _search_payload() -> dict:
    return {
        "results": [
            {
                "media_type": "movie",
                "id": 1,
                "title": "Inception",
                "original_title": "Inception",
                "release_date": "2010-07-15",
            },
            {
                "media_type": "tv",
                "id": 2,
                "name": "Breaking Bad",
                "original_name": "Breaking Bad",
                "first_air_date": "2008-01-20",
            },
            {"media_type": "person", "id": 3, "name": "Christopher Nolan"},
        ]
    }


class SearchTests(unittest.TestCase):
    def test_filters_to_movie_and_tv(self) -> None:
        with mock.patch.object(movie, "_tmdb_get", return_value=_search_payload()):
            results = movie.search("x", language="zh-CN")
        self.assertEqual([r["media_type"] for r in results], ["movie", "tv"])

    def test_type_filter(self) -> None:
        with mock.patch.object(movie, "_tmdb_get", return_value=_search_payload()):
            results = movie.search("x", language="zh-CN", kind="tv")
        self.assertEqual([r["media_type"] for r in results], ["tv"])


class FetchTitleTests(unittest.TestCase):
    def test_tv_seasons_filtered_and_sorted(self) -> None:
        payload = {
            "name": "绝命毒师",
            "original_name": "Breaking Bad",
            "poster_path": "/abc.jpg",
            "seasons": [
                {"season_number": 2, "episode_count": 13, "name": "Season 2"},
                {"season_number": 0, "episode_count": 0, "name": "Specials"},
                {"season_number": 1, "episode_count": 7, "name": "Season 1"},
            ],
        }
        with mock.patch.object(movie, "_tmdb_get", return_value=payload):
            title = movie.fetch_title("tv", 2, language="zh-CN")
        self.assertEqual(title.kind, "tv")
        self.assertEqual(title.name, "绝命毒师")
        self.assertEqual(title.poster_path, "/abc.jpg")
        # 0-episode season dropped; remaining sorted 1, 2
        self.assertEqual([s.number for s in title.seasons], [1, 2])
        self.assertEqual([s.episodes for s in title.seasons], [7, 13])

    def test_specials_sort_last_when_present(self) -> None:
        payload = {
            "name": "show",
            "original_name": "show",
            "poster_path": None,
            "seasons": [
                {"season_number": 0, "episode_count": 3, "name": "Specials"},
                {"season_number": 2, "episode_count": 10, "name": "S2"},
                {"season_number": 1, "episode_count": 6, "name": "S1"},
            ],
        }
        with mock.patch.object(movie, "_tmdb_get", return_value=payload):
            title = movie.fetch_title("tv", 1, language="zh-CN")
        # regular seasons first (1, 2), then specials (0)
        self.assertEqual([s.number for s in title.seasons], [1, 2, 0])

    def test_movie_has_no_seasons(self) -> None:
        payload = {
            "title": "盗梦空间",
            "original_title": "Inception",
            "poster_path": "/xyz.jpg",
        }
        with mock.patch.object(movie, "_tmdb_get", return_value=payload):
            title = movie.fetch_title("movie", 1, language="zh-CN")
        self.assertEqual(title.kind, "movie")
        self.assertEqual(title.seasons, ())


if __name__ == "__main__":
    unittest.main()
