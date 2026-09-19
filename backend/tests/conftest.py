import pytest
import asyncio
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.base import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_vertex_response():
    """Factory for mock Vertex AI (Gemini) responses."""
    def _make(content: str, tokens_in: int = 100, tokens_out: int = 200):
        mock_response = MagicMock()
        mock_response.text = content
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = tokens_in
        mock_usage.candidates_token_count = tokens_out
        mock_response.usage_metadata = mock_usage
        return mock_response
    return _make


@pytest.fixture
def sample_transcript():
    return """Meeting: Q4 Planning
Attendees: Sarah (PM), Mike (Engineering)

Sarah: We need to launch the dashboard by December 15th.
Mike: I'll assign Alex to lead it. Budget is $30,000.
Sarah: Agreed. Make sure it passes security review before deployment."""


@pytest.fixture
def sample_rules():
    return """Company Rules:
1. All deployments require security review sign-off.
2. Budget must not exceed approved amount.
3. Code freeze must be 2 weeks before release."""
