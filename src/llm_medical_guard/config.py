"""Configuration for medical guard."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GuardConfig:
    """Configuration for MedicalGuard."""

    locale: str = "en"
    strict: bool = False
    checks_enabled: dict[str, bool] = field(default_factory=dict)
    custom_banned_expressions: list[str] = field(default_factory=list)
    custom_brands: list[str] = field(default_factory=list)
    custom_disclaimer_patterns: list[str] = field(default_factory=list)
    custom_safe_alternatives: dict[str, str] = field(default_factory=dict)
    _locale_data: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_yaml(cls, path: str | Path) -> GuardConfig:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GuardConfig:
        return cls(
            locale=data.get("locale", "en"),
            strict=data.get("strict", False),
            checks_enabled=data.get("checks", {}),
            custom_banned_expressions=data.get("custom_banned_expressions", []),
            custom_brands=data.get("custom_brands", []),
            custom_disclaimer_patterns=data.get("custom_disclaimer_patterns", []),
            custom_safe_alternatives=data.get("custom_safe_alternatives", {}),
        )

    def load_locale(self) -> dict[str, Any]:
        if self._locale_data:
            return self._locale_data
        locale_dir = Path(__file__).parent / "i18n"
        locale_file = locale_dir / f"{self.locale}.yaml"
        if not locale_file.exists():
            locale_file = locale_dir / "en.yaml"
        with open(locale_file, encoding="utf-8") as f:
            self._locale_data = yaml.safe_load(f) or {}
        return self._locale_data
