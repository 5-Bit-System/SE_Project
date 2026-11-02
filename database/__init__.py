"""HUS/Neon database module for the AI-07 course recommender.

This package documents, inspects, verifies and imports the *other* PostgreSQL
design used by the project: the HUS training-portal prototype hosted on Neon
(database ``ai07``, schema ``public``). It is intentionally separate from the
``app`` runtime schema (``app/db``): both exist, but they describe different
things and must not be mixed.
"""
