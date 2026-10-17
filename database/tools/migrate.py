"""Apply the separate HUS migration history: python -m database.tools.migrate upgrade."""

from __future__ import annotations

import argparse
from pathlib import Path

from alembic.config import Config

from alembic import command


def config() -> Config:
    root = Path(__file__).resolve().parents[2]
    cfg = Config(str(root / "database" / "hus_alembic.ini"))
    cfg.set_main_option("script_location", str(root / "database" / "hus_alembic"))
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate the HUS database")
    parser.add_argument("action", choices=("upgrade", "current", "heads"))
    args = parser.parse_args()
    cfg = config()
    if args.action == "upgrade":
        command.upgrade(cfg, "head")
    elif args.action == "current":
        command.current(cfg)
    else:
        command.heads(cfg)


if __name__ == "__main__":
    main()
