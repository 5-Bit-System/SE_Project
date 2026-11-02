"""Malformed source data must fail before opening a database connection."""

from copy import deepcopy

import pytest

from database.tools.publish_catalogs import publish_catalogs


@pytest.mark.parametrize("table,key,value,message", [
    ("majors", "faculty_code", "MISSING", "missing faculty"),
    ("curricula", "major_code", "MISSING", "curriculum identity"),
    ("curriculum_courses", "course_code", "MISSING", "course relationship"),
    ("curriculum_courses", "course_group", "MISSING", "official group"),
    ("official_curriculum_groups", "curriculum_id", -1, "official group"),
    ("official_curriculum_entries", "group_key", "MISSING", "membership or group"),
    ("official_curriculum_entries", "credits_in_source", 99, "source credits"),
    ("course_prerequisites", "prerequisite_course_code", "MISSING", "prerequisite relationship"),
    ("course_prerequisites", "group_no", 0, "prerequisite relationship"),
])
def test_invalid_relationship_prevents_publication(source_bundle, table, key, value, message):
    broken = deepcopy(source_bundle)
    broken["tables"][table][0][key] = value
    with pytest.raises(ValueError, match=message):
        publish_catalogs(None, broken)  # No engine: validation must happen before any writes.


@pytest.mark.parametrize("table", [
    "faculties", "majors", "curricula", "courses", "curriculum_courses",
    "course_prerequisites", "official_curriculum_groups", "official_curriculum_entries",
])
def test_duplicate_keys_prevent_publication(source_bundle, table):
    broken = deepcopy(source_bundle)
    broken["tables"][table].append(deepcopy(broken["tables"][table][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        publish_catalogs(None, broken)


def test_self_prerequisite_prevents_publication(source_bundle):
    broken = deepcopy(source_bundle)
    row = broken["tables"]["course_prerequisites"][0]
    row["prerequisite_course_code"] = row["course_code"]
    with pytest.raises(ValueError, match="Self prerequisite"):
        publish_catalogs(None, broken)
