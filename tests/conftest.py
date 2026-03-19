"""Shared test fixtures."""

import pytest

from llm_medical_guard import MedicalGuard


@pytest.fixture
def guard_en():
    return MedicalGuard(locale="en")


@pytest.fixture
def guard_ko():
    return MedicalGuard(locale="ko")


@pytest.fixture
def guard_ja():
    return MedicalGuard(locale="ja")


@pytest.fixture
def strict_guard():
    return MedicalGuard(locale="en", strict=True)
