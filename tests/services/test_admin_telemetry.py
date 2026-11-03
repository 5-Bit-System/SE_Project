import asyncio

import pytest

from app.services.operational_metrics import measured_consultation, metrics_recorder


def test_consultation_records_success_failure_without_sensitive_content():
    asyncio.run(exercise_consultations())


async def exercise_consultations():
    from fastapi import HTTPException
    metrics_recorder.clear()
    @measured_consultation('recommendation')
    async def successful():
        return {'ok': True}
    @measured_consultation('recommendation')
    async def failed():
        raise HTTPException(409, 'private-student-details')
    assert await successful() == {'ok': True}
    with pytest.raises(HTTPException):
        await failed()
    health = metrics_recorder.get_health()
    assert health['consultation_health']['total_consultations'] == 2
    assert health['consultation_health']['failed_consultations'] == 1
    assert 'private-student-details' not in str(health)
    assert health['scope'] == 'current_process' and health['started_at']
    metrics_recorder.clear()
