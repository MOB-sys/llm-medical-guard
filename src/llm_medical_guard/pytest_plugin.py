"""pytest plugin for llm-medical-guard.

Usage:
    # In conftest.py
    pytest_plugins = ["llm_medical_guard.pytest_plugin"]

    # In tests
    def test_health_article(medical_guard):
        result = medical_guard.check("Your health article content here...")
        assert result.passed

    # Or use the marker
    @pytest.mark.medical_guard(locale="ko", strict=True)
    def test_korean_content(medical_guard):
        result = medical_guard.check("한국어 건강 콘텐츠...")
        assert result.passed

CLI Usage:
    pytest --medical-guard           # Enable medical guard checks
    pytest --medical-guard-locale=ko # Set locale
    pytest --medical-guard-strict    # Fail on any guard warning
"""

from __future__ import annotations

from typing import Any

import pytest

from llm_medical_guard.guard import MedicalGuard


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("medical-guard", "Medical content guardrails")
    group.addoption(
        "--medical-guard",
        action="store_true",
        default=False,
        help="Enable medical guard fixture.",
    )
    group.addoption(
        "--medical-guard-locale",
        default="en",
        help="Locale for medical guard (default: en).",
    )
    group.addoption(
        "--medical-guard-strict",
        action="store_true",
        default=False,
        help="Strict mode: fail on any guard issue.",
    )


@pytest.fixture
def medical_guard(request: Any) -> MedicalGuard:
    """Fixture providing a configured MedicalGuard instance.

    Reads configuration from:
    1. @pytest.mark.medical_guard marker kwargs
    2. CLI options (--medical-guard-locale, --medical-guard-strict)
    3. Defaults
    """
    locale = request.config.getoption("--medical-guard-locale", "en")
    strict = request.config.getoption("--medical-guard-strict", False)

    # Check for marker overrides
    marker = request.node.get_closest_marker("medical_guard")
    if marker:
        locale = marker.kwargs.get("locale", locale)
        strict = marker.kwargs.get("strict", strict)

    return MedicalGuard(locale=locale, strict=strict)


def pytest_configure(config: Any) -> None:
    config.addinivalue_line(
        "markers",
        "medical_guard(locale, strict): configure medical guard for this test",
    )
