"""Report checked-in source coverage; never connects to a runtime database."""

import json
from pathlib import Path

from database.hus_db.catalog_builder import build_catalogs


def main():
    root = Path(__file__).resolve().parents[1]
    catalogs = build_catalogs(json.loads((root / "database/data/hus_source.json").read_text()))
    fields = ("topics", "career_paths", "orientation", "difficulty", "workload")
    print(json.dumps({"scope": "checked-in source only; not runtime DB or review certification",
        "programs": [{"program_id": c.program.program_id, "memberships": len(c.courses),
                      "nonempty": {f: sum(bool(getattr(row, f)) for row in c.courses) for f in fields}}
                     for c in catalogs]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
