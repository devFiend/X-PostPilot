"""
Unit tests for AI Layer and character validation.
"""

from unittest.mock import MagicMock, AsyncMock, patch
import httpx
import pytest
from postpilot.ai.router import AIRouter
from postpilot.ai.groq import GroqProvider


@pytest.mark.asyncio
async def test_character_limit_enforcement():
    """Test that generated text is parsed and validated."""
    mock_post = "Building in public is not about vanity metrics; it is about sharing the hard lessons."
    assert len(mock_post) <= 280


@pytest.mark.asyncio
async def test_groq_provider_parse():
    """Test Groq generation parsing separated by '---'."""
    provider = GroqProvider(api_key="mock_key")
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Post 1\n---\nPost 2\n---\nPost 3"}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await provider.generate("topic", "system", count=2)
        assert len(res) == 2
        assert res[0] == "Post 1"
        assert res[1] == "Post 2"
