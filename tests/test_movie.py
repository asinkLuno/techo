import re
import unittest
from unittest import mock

from src.movie import movie


def _printed(joined: str) -> str:
    """Node contents in document order, concatenated.

    Season labels and the title are printed one glyph per cell, so ``S01`` lives in
    the token stream as ``S`` ``0`` ``1`` rather than a contiguous substring. Reading
    the cells back in order reconstructs the readable text.
    """
    return "".join(re.findall(r"\\node[^{]*\{([^{}]*)\};", joined))


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


class GeometryTests(unittest.TestCase):
    def test_known_size_keys(self) -> None:
        # 74m5: 74×105, binding 12 / right 5 / top 4 / bottom 9, 5mm step → 11×18 centered at (13, 5).
        geo = movie._grid_geometry("74m5", 74.0, 105.0)
        self.assertEqual((geo.num_x, geo.num_y, geo.step), (11, 18, 5.0))
        self.assertEqual((geo.start_x, geo.start_y), (13.0, 5.0))

    def test_unknown_size_falls_back(self) -> None:
        geo = movie._grid_geometry("does-not-exist", 74.0, 105.0)
        # default margins (12/5/5/5) → usable 57×95 → 11×19
        self.assertEqual((geo.num_x, geo.num_y, geo.step), (11, 19, 5.0))


class PrintTextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.geo = movie._grid_geometry("74m5", 74.0, 105.0)

    def test_one_node_per_non_space_char(self) -> None:
        nodes, rows = movie._print_text(self.geo, 0, "abc", "FontSmall")
        self.assertEqual(len(nodes), 3)
        self.assertEqual(rows, 1)
        self.assertTrue(all("\\node" in n for n in nodes))

    def test_wraps_at_num_x_and_skips_spaces(self) -> None:
        # 12 non-space chars at 11 cols → 2 rows; the space occupies a cell but prints nothing.
        nodes, rows = movie._print_text(self.geo, 0, "a" * 11 + " b", "FontSmall")
        self.assertEqual(len(nodes), 12)  # 11 'a' + 1 'b', space printed nothing
        self.assertEqual(rows, 2)

    def test_empty(self) -> None:
        self.assertEqual(movie._print_text(self.geo, 0, "", "FontSmall"), ([], 0))
        self.assertEqual(movie._print_text(self.geo, 0, None, "FontSmall"), ([], 0))


class PrintNumbersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.geo = movie._grid_geometry("74m5", 74.0, 105.0)

    def test_one_node_per_number(self) -> None:
        nodes, rows = movie._print_numbers(self.geo, 0, list(range(1, 11)), "FontSmall")
        self.assertEqual(len(nodes), 10)
        self.assertEqual(rows, 1)
        self.assertTrue(all("\\node" in n for n in nodes))
        self.assertIn("{1}", nodes[0])
        self.assertIn("{10}", nodes[-1])

    def test_wraps_rows(self) -> None:
        # 13 numbers at 11 cols → 2 rows
        _, rows = movie._print_numbers(self.geo, 0, list(range(1, 14)), "FontSmall")
        self.assertEqual(rows, 2)


class StarsRowTests(unittest.TestCase):
    def test_five_glyphs_one_per_cell(self) -> None:
        geo = movie._grid_geometry("74m5", 74.0, 105.0)
        nodes = movie._stars_row(geo, 2)
        self.assertEqual(len(nodes), 5)
        self.assertEqual("".join(nodes).count("☆"), 5)


class BackgroundTests(unittest.TestCase):
    def test_background_emits_draws(self) -> None:
        geo = movie._grid_geometry("74m5", 74.0, 105.0)
        lines = movie._grid_background(geo)
        self.assertTrue(lines)
        self.assertTrue(any("\\draw" in ln for ln in lines))
        # page-corner anchored, like the content nodes
        self.assertTrue(all("current page.north west" in ln for ln in lines))


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
        # labels are printed one glyph per cell; reconstruct from the cell order
        text = _printed(joined)
        self.assertIn("S01", text)
        self.assertIn("S02", text)

    def test_background_grid_on_every_page(self) -> None:
        seasons = tuple(movie.Season(n, 13, f"S{n}") for n in range(1, 21))
        pages = movie._pack_seasons(seasons, "74m5", 74.0, 105.0)
        # each page carries the full-page midori background
        for page in pages:
            joined = "\n".join(page)
            self.assertIn("\\draw", joined)

    def test_preserves_given_season_order(self) -> None:
        # sorting (specials last) is fetch_title's job; _pack_seasons keeps given order
        seasons = (movie.Season(1, 7, "S1"), movie.Season(0, 3, "Specials"))
        pages = movie._pack_seasons(seasons, "74m5", 74.0, 105.0)
        joined = "\n".join("\n".join(p) for p in pages)
        text = _printed(joined)
        self.assertIn("S00", text)
        self.assertLess(text.index("S01"), text.index("S00"))


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
        self.assertEqual(
            (kind, name, original, year), ("movie", "盗梦空间", "Inception", "2010")
        )

    def test_tv(self) -> None:
        kind, name, original, year = movie._result_summary(
            {
                "media_type": "tv",
                "name": "绝命毒师",
                "original_name": "Breaking Bad",
                "first_air_date": "2008-01-20",
            }
        )
        self.assertEqual(
            (kind, name, original, year), ("tv", "绝命毒师", "Breaking Bad", "2008")
        )

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
