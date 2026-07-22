import unittest

from src.ebook.extract import _safe_name
from src.ebook.split import _safe
from src.midori_grid.midori_grid import _dot_indices, grid_lines


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


if __name__ == "__main__":
    unittest.main()
