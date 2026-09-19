import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def mock_db():
    """Mock database session."""
    session = AsyncMock()
    return session


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["app"] == "MA2"


class TestRunCreateValidation:
    @pytest.mark.asyncio
    async def test_empty_transcript_rejected(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/runs",
                json={"transcript": "", "rules": "some rules"},
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_rules_rejected(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/runs",
                json={"transcript": "some transcript", "rules": ""},
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_fields_rejected(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/runs", json={})
            assert response.status_code == 422


class TestSimulateFailureValidation:
    def test_invalid_step_rejected(self):
        from app.schemas.run import SimulateFailureRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SimulateFailureRequest(step="invalid")

    def test_valid_steps_accepted(self):
        from app.schemas.run import SimulateFailureRequest

        for step in ["intake", "planning", "review"]:
            req = SimulateFailureRequest(step=step)
            assert req.step == step
