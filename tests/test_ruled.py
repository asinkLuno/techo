import unittest

from techo.ruled.ruled import content


class RuledContentTests(unittest.TestCase):
    def test_content_is_one_empty_page(self) -> None:
        self.assertEqual(
            content(),
            [
                "\\thispagestyle{empty}%",
                "\\null",
                "\\clearpage",
            ],
        )


if __name__ == "__main__":
    unittest.main()