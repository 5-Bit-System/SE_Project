"""Offline regression for databases with previously published revision IDs."""

import pytest
from alembic.script import ScriptDirectory

from database.tools.migrate import config


@pytest.mark.parametrize(('current', 'expected'), [
    ('hus_20261023_04', {
        'hus_20261025_04', 'hus_20261025_05', 'hus_20261025_06', 'hus_20261028_07',
    }),
    ('hus_20261025_06', {
        'hus_20261023_01', 'hus_20261023_04', 'hus_20261028_07',
    }),
])
def test_upgrade_from_deployed_heads_does_not_replay_applied_ddl(current, expected):
    scripts = ScriptDirectory.from_config(config())
    assert scripts.get_heads() == ['hus_20261028_07']
    plan = scripts._upgrade_revs('head', current)
    assert {step.revision.revision for step in plan} == expected


def test_fresh_database_has_one_merged_upgrade_path():
    scripts = ScriptDirectory.from_config(config())
    plan = scripts._upgrade_revs('head', 'base')
    revisions = [step.revision.revision for step in plan]
    assert len(revisions) == len(set(revisions))
    assert revisions[-1] == 'hus_20261028_07'
    assert {'hus_20261023_01', 'hus_20261023_03', 'hus_20261025_06'} <= set(revisions)
