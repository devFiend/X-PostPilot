"""
Unit tests for Autopilot Service.
"""

from unittest.mock import AsyncMock, patch
import pytest
from postpilot.database.repositories import SettingsRepository
from postpilot.services.autopilot import AutopilotService


def test_autopilot_pause_resume(in_memory_db):
    service = AutopilotService(in_memory_db)
    assert not service.is_paused()

    service.pause()
    assert service.is_paused()

    service.resume()
    assert not service.is_paused()


def test_autopilot_enable_disable(in_memory_db):
    service = AutopilotService(in_memory_db)
    service.enable()
    assert service.is_enabled()

    service.disable()
    assert not service.is_enabled()


@pytest.mark.asyncio
async def test_autopilot_cycle_when_disabled(in_memory_db):
    service = AutopilotService(in_memory_db)
    # Disabled by default
    with pytest.raises(RuntimeError, match="Autopilot is disabled"):
        await service.execute_cycle()
