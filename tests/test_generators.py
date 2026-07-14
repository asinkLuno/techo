import unittest

from src.ebook.extract import _safe_name
from src.ebook.split import _safe
from src.midori_grid.midori_grid import _dot_indices


class GeneratorHelperTests(unittest.TestCase):
    def test_safe_names(self) -> None:
        self.assertEqual(_safe_name("a/b::c"), "a_b_c")
        self.assertEqual(_safe("a/b::c"), "a_b_c")

    def test_dot_indices_are_symmetric_and_exclude_borders(self) -> None:
        self.assertEqual(_dot_indices(20, 5), {5, 10, 15})
        self.assertEqual(_dot_indices(4, 10), {2})


if __name__ == "__main__":
    unittest.main()
