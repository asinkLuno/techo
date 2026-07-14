"""Small, reusable parsers for command and library inputs."""

from datetime import date


def parse_year_month(value: str) -> tuple[int, int]:
    """Parse YYYY-MM and reject impossible or non-canonical values."""
    try:
        year_text, month_text = value.split("-")
        year, month = int(year_text), int(month_text)
        date(year, month, 1)
    except (TypeError, ValueError) as error:
        raise ValueError(f"expected YYYY-MM (e.g. 2026-07), got {value!r}") from error
    if len(year_text) != 4 or len(month_text) != 2:
        raise ValueError(f"expected YYYY-MM (e.g. 2026-07), got {value!r}")
    return year, month


def parse_date(value: str) -> date:
    """Parse a canonical ISO calendar date."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"expected YYYY-MM-DD (e.g. 2026-07-15), got {value!r}"
        ) from error
    if parsed.isoformat() != value:
        raise ValueError(f"expected YYYY-MM-DD, got {value!r}")
    return parsed


def location_coordinates(
    name: str, locations: dict[str, tuple[float, float]]
) -> tuple[float, float]:
    """Look up a named location with a useful domain error."""
    try:
        return locations[name]
    except KeyError as error:
        known = ", ".join(locations)
        raise ValueError(
            f"unknown location {name!r}; known locations: {known}"
        ) from error
