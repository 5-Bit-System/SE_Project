"""Profile the real JSON loader/search path on the unchanged HTTP fixture."""

import cProfile
import os
import pstats
import tempfile
from pathlib import Path

from tools.bt3.http_fixture import PROGRAM, write_fixture


def main():
    os.environ.update(STORAGE_BACKEND="json", DATABASE_MODEL="hus", DATABASE_URL="",
                      RECOMMENDATION_LLM_ENABLED="false", GEMINI_API_KEY="")
    from app.catalog import load_catalog
    from app.services.course_search_service import search_courses

    with tempfile.TemporaryDirectory(prefix="bt3-profile-") as directory:
        root = Path(directory)
        write_fixture(root)
        profiler = cProfile.Profile()
        with profiler:
            for _ in range(500):
                catalog = load_catalog(PROGRAM, root=root)
                search_courses(catalog, q="systems", sort="credits", page=2, page_size=15)
        pstats.Stats(profiler).strip_dirs().sort_stats("cumulative").print_stats(25)


if __name__ == "__main__":
    main()
