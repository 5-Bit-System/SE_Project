"""Keep table cells as text until the authenticated transcript format is verified."""

from app.integrations.daotao.text import repair_source_text


def normalize_rows(rows: list[list[str]]) -> list[list[str]]:
    """Repair course names before whitespace can destroy recoverable bytes."""
    normalized = []
    for row in rows:
        course_row = len(row) >= 7 and row[0].strip().isdigit() and row[1].strip()
        normalized.append([
            " ".join((repair_source_text(cell) if course_row and index == 2 else cell).split())
            for index, cell in enumerate(row)
        ])
    return [row for row in normalized if any(row)]
