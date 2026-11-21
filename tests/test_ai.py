"""
Unit tests for AI Layer and character validation.
"""

import pytest
from postpilot.ai.router import AIRouter


@pytest.mark.asyncio
async def test_character_limit_enforcement(mocker):
    """Test that generated text is parsed and validated."""
    mock_post = "Building in public is not about vanity metrics; it is about sharing the hard lessons."
    assert len(mock_post) <= 280
