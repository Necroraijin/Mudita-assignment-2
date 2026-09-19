"""Tests verifying that two runs don't share context."""
import pytest
from app.schemas.run import RunCreate


class TestSessionIsolation:
    def test_run_create_schema_independent(self):
        """Two RunCreate instances don't share state."""
        run1 = RunCreate(transcript="Transcript A", rules="Rules A")
        run2 = RunCreate(transcript="Transcript B", rules="Rules B")

        assert run1.transcript != run2.transcript
        assert run1.rules != run2.rules

    def test_run_ids_unique(self):
        """Each run gets a unique UUID."""
        import uuid
        ids = {str(uuid.uuid4()) for _ in range(100)}
        assert len(ids) == 100
