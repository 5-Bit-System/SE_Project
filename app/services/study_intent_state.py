"""Ephemeral normalized state attached to an existing authenticated runtime session.

No raw history or cross-session database state. Restarts/context changes require
confirmation instead of treating lost limits as unlimited. CAS rejects late turns.
"""

from app.schemas.study_intent import StudyIntentState


class IntentStateConflict(ValueError):
    pass


def begin(value, context_key: str, *, expected_version=None, reset=False, has_history=False):
    record = getattr(value, "study_intent", None)
    version = record["version"] if record else 0
    if expected_version is not None and expected_version != version:
        raise IntentStateConflict("intent_version_changed")
    if reset:
        state = StudyIntentState()
    elif record and record["context"] == context_key:
        state = record["state"].model_copy(deep=True)
    elif record or has_history or expected_version:
        state = StudyIntentState(questions=["context: trạng thái cũ không còn hợp lệ; hãy bắt đầu lại hội thoại và xác nhận giới hạn."])
    else:
        state = StudyIntentState()
    return version, state


def commit(value, context_key: str, version: int, state: StudyIntentState):
    current = getattr(value, "study_intent", None)
    if (current["version"] if current else 0) != version:
        raise IntentStateConflict("intent_version_changed")
    value.study_intent = {"context": context_key, "version": version + 1,
                          "state": state.model_copy(deep=True)}
    return version + 1
