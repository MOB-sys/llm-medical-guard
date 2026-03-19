"""Tests for pytest plugin."""

import pytest

from llm_medical_guard import MedicalGuard


class TestPytestPlugin:
    def test_medical_guard_fixture(self, medical_guard):
        """Test that the medical_guard fixture works."""
        assert isinstance(medical_guard, MedicalGuard)
        result = medical_guard.check(
            "Vitamin D is healthy. Not a substitute for professional medical advice. Source: NIH."
        )
        assert result.passed

    def test_fixture_catches_issues(self, medical_guard):
        """Test that the fixture catches medical content issues."""
        result = medical_guard.check("This miracle cure has no side effects!")
        assert not result.passed
