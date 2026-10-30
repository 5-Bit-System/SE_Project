"""Pure-service ordering and shared-state checks, supplementing test-first API contracts."""

import itertools

import pytest

from app.services.course_search_service import search_courses
from tests.support.search_data import CODE_ORDER, CREDIT_ORDER, NAME_ORDER, search_catalog


@pytest.mark.parametrize(("sort", "expected"), [
    ("code", CODE_ORDER), ("name", NAME_ORDER), ("credits", CREDIT_ORDER),
])
def test_total_order_survives_all_permutations_of_tied_rows(sort, expected):
    catalog = search_catalog()
    tied = [course for course in catalog.courses if course.code in {"C01", "C02", "C04", "C08"}]
    other = [course for course in catalog.courses if course not in tied]
    for permutation in itertools.permutations(tied):
        catalog.courses = [*permutation, *other]
        actual = search_courses(catalog, sort=sort)
        assert [course.code for course in actual.items] == expected


def test_repeated_filter_sort_page_does_not_mutate_shared_catalog():
    catalog = search_catalog()
    before = catalog.model_dump(mode="json")
    for _ in range(10):
        assert [c.code for c in search_courses(catalog, sort="credits", page_size=2).items] == ["C06", "C05"]
        assert [c.code for c in search_courses(catalog, q="data", block="major",
                                             requirement_type="elective").items] == ["C02", "C04"]
        assert not search_courses(catalog, q="missing").items
    assert catalog.model_dump(mode="json") == before
