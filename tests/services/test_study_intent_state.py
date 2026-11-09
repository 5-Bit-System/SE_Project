from types import SimpleNamespace

import pytest

from app.schemas.study_intent import StudyIntentState
from app.services.study_intent_state import IntentStateConflict, begin, commit


def test_session_revision_cas_and_restart_require_confirmation():
    session = SimpleNamespace()
    version, first = begin(session, "program-a-revision-1")
    assert version == 0 and not first.questions
    assert commit(session, "program-a-revision-1", version,
                  StudyIntentState(values={"target_credits": 3})) == 1
    _, current = begin(session, "program-a-revision-1", expected_version=1)
    assert current.values["target_credits"] == 3
    _, switched = begin(session, "program-b-revision-1")
    assert switched.questions and not switched.values
    with pytest.raises(IntentStateConflict):
        commit(session, "program-a-revision-1", 0, first)
    with pytest.raises(IntentStateConflict):
        begin(session, "program-a-revision-1", expected_version=0)
    _, restarted = begin(SimpleNamespace(), "program-a-revision-1", has_history=True)
    assert restarted.questions
    _, reset = begin(session, "program-b-revision-1", reset=True)
    assert not reset.questions and not reset.values


def test_state_is_copied_and_other_account_session_cannot_inherit():
    first, other = SimpleNamespace(), SimpleNamespace()
    state = StudyIntentState(values={"target_credits": 3})
    commit(first, "revision", 0, state)
    state.values["target_credits"] = 30
    _, retained = begin(first, "revision")
    assert retained.values["target_credits"] == 3
    _, unrelated = begin(other, "revision")
    assert not unrelated.values
