import unittest

from techo.ebook.extract import _safe_name
from techo.ebook.split import _safe
from techo.midori_grid.midori_grid import _dot_indices, grid_lines
from techo.timeline.timeline import content, page_range


class GeneratorHelperTests(unittest.TestCase):
    def test_safe_names(self) -> None:
        self.assertEqual(_safe_name("a/b::c"), "a_b_c")
        self.assertEqual(_safe("a/b::c"), "a_b_c")

    def test_dot_indices_are_symmetric_and_exclude_borders(self) -> None:
        self.assertEqual(_dot_indices(20, 5), {5, 10, 15})
        self.assertEqual(_dot_indices(4, 10), {2})

    def test_grid_lines_anchors_via_coord_fn(self) -> None:
        # a 2×2 grid: 3 horizontals + 3 verticals = 6 draws; coord fn controls the point format
        lines = grid_lines(
            0.0,
            0.0,
            2,
            2,
            step=5.0,
            gap=1.0,
            ext=1.2,
            dot_freq=10,
            coord=lambda x, y: f"<{x:.1f},{y:.1f}>",
        )
        draws = [ln for ln in lines if "\\draw" in ln]
        self.assertEqual(len(draws), 6)
        self.assertIn("<0.0,0.0>", draws[0])


    def test_page_range_split_and_swap(self) -> None:
        # full range on every page when pages=1
        self.assertEqual(page_range(0, 26, 1, False, True), (0, 26))
        self.assertEqual(page_range(0, 26, 1, False, False), (0, 26))
        # pages=2: even/left page gets the first half, odd/right the second
        self.assertEqual(page_range(0, 26, 2, False, False), (0, 13))
        self.assertEqual(page_range(0, 26, 2, False, True), (13, 26))
        # swap exchanges the halves
        self.assertEqual(page_range(0, 26, 2, True, False), (13, 26))
        self.assertEqual(page_range(0, 26, 2, True, True), (0, 13))

    def test_timeline_content_calls(self) -> None:
        # odd page first, even page second; the LaTeX macro owns the side
        self.assertEqual(
            content(0, 26, 2),
            ["\\timelinepage{13}{26}", "\\timelinepage{0}{13}"],
        )
        self.assertEqual(
            content(0, 26, 2, swap=True),
            ["\\timelinepage{0}{13}", "\\timelinepage{13}{26}"],
        )
        self.assertEqual(
            content(6, 22, 1),
            ["\\timelinepage{6}{22}", "\\timelinepage{6}{22}"],
        )

if __name__ == "__main__":
    unittest.main()
