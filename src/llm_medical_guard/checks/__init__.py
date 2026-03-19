"""Check registry and base class for medical guard checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from llm_medical_guard.result import CheckResult

if TYPE_CHECKING:
    from llm_medical_guard.config import GuardConfig


class BaseCheck(ABC):
    """Base class for all medical guard checks."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, text: str, config: GuardConfig) -> CheckResult:
        ...


class CheckRegistry:
    """Registry of available checks."""

    _checks: dict[str, type[BaseCheck]] = {}

    @classmethod
    def register(cls, check_cls: type[BaseCheck]) -> type[BaseCheck]:
        cls._checks[check_cls.name] = check_cls
        return check_cls

    @classmethod
    def get_all(cls) -> dict[str, type[BaseCheck]]:
        return dict(cls._checks)

    @classmethod
    def get_enabled(cls, config: GuardConfig) -> list[BaseCheck]:
        enabled = []
        for name, check_cls in cls._checks.items():
            if config.checks_enabled.get(name, True):
                enabled.append(check_cls())
        return enabled
