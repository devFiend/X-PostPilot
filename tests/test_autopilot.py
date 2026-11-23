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


@pytest.mark.asyncio
async def test_autopilot_cycle_rotates_pillars_and_archetypes(in_memory_db):
    from postpilot.database.models import CreatorProfile, Draft
    profile = CreatorProfile(
        name="Builder",
        tone="Direct",
        content_pillars="Micro-SaaS, Python Architecture, AI Agents",
    )
    in_memory_db.add(profile)
    in_memory_db.commit()

    service = AutopilotService(in_memory_db)
    service.enable()

    with patch.object(service.content_service, "generate_drafts", new_callable=AsyncMock) as mock_gen:
        mock_draft1 = Draft(id=1, content="Post 1", topic="Micro-SaaS", category="educational", character_count=6)
        mock_draft2 = Draft(id=2, content="Post 2", topic="Python Architecture", category="developer observations", character_count=6)
        mock_gen.side_effect = [[mock_draft1], [mock_draft2]]

        # Cycle 1
        drafts1 = await service.execute_cycle()
        assert len(drafts1) == 1
        first_call = mock_gen.call_args_list[0].kwargs
        assert first_call["topic"] == "Micro-SaaS"
        assert "archetype" in first_call

        # Cycle 2 should rotate to next pillar
        drafts2 = await service.execute_cycle()
        assert len(drafts2) == 1
        second_call = mock_gen.call_args_list[1].kwargs
        assert second_call["topic"] == "Python Architecture"
        assert second_call["archetype"] != first_call["archetype"]

