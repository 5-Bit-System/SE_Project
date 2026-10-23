"""Keep table cells as text until the authenticated transcript format is verified."""


def normalize_rows(rows: list[list[str]]) -> list[list[str]]:
    """Normalize whitespace without guessing column meanings or grade values."""
    normalized = [[" ".join(cell.split()) for cell in row] for row in rows]
    return [row for row in normalized if any(row)]
