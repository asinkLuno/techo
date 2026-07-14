import unittest
from datetime import date

from click.testing import CliRunner

from src.cli import cli
from src.validation import location_coordinates, parse_date, parse_year_month


class ValidationTests(unittest.TestCase):
    def test_parse_year_month(self) -> None:
        self.assertEqual(parse_year_month("2026-07"), (2026, 7))

    def test_parse_year_month_rejects_noncanonical_and_impossible_values(self) -> None:
        for value in ("2026-7", "2026-13", "hello"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_year_month(value)

    def test_parse_date(self) -> None:
        self.assertEqual(parse_date("2024-02-29"), date(2024, 2, 29))

    def test_parse_date_rejects_impossible_date(self) -> None:
        with self.assertRaises(ValueError):
            parse_date("2025-02-29")

    def test_location_coordinates(self) -> None:
        locations = {"home": (1.0, 2.0)}
        self.assertEqual(location_coordinates("home", locations), (1.0, 2.0))
        with self.assertRaisesRegex(ValueError, "known locations: home"):
            location_coordinates("away", locations)

    def test_cli_turns_domain_error_into_click_error(self) -> None:
        result = CliRunner().invoke(cli, ["senary", "2026-13"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: expected YYYY-MM", result.output)


if __name__ == "__main__":
    unittest.main()
