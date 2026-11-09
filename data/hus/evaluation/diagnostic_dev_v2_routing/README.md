# Diagnostic dev v2 — routing slice

Eight already-exposed requests copied verbatim from H2 before runtime tuning:
four course-name lookups and four course-content previews, across four majors.
Gold/evidence are inherited from direct pinned source review, never predictions.
This is development data, not an independent holdout. Original H2/P11/P12/P2,
review/source packages and runtime data remain unchanged.

Scope: name/code intent and distinguishing a preview before a course from real
prerequisite requests. Consent/scope/source-review remain enforced. A correct
route does not establish answer support: the post-retrieval gate is priority2.
Before/after runs must save requests and actual classifier/search observations;
do not force expected fields or course IDs into the requests. Use fresh run dirs.
