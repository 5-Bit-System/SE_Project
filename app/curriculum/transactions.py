"""Serialize catalog/source changes with the canonical HUS publisher."""
from sqlalchemy import text


def publication_lock(conn):
    conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('ai07_hus_catalog_publish'))"))
