"""Tests for configuration."""

import tempfile
from pathlib import Path

import yaml

from llm_medical_guard.config import GuardConfig


class TestConfig:
    def test_default_config(self):
        config = GuardConfig()
        assert config.locale == "en"
        assert config.strict is False

    def test_from_dict(self):
        config = GuardConfig.from_dict({
            "locale": "ko",
            "strict": True,
            "checks": {"dosage": False},
        })
        assert config.locale == "ko"
        assert config.strict is True
        assert config.checks_enabled.get("dosage") is False

    def test_from_yaml(self):
        data = {
            "locale": "en",
            "strict": False,
            "custom_banned_expressions": ["snake oil"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = f.name

        config = GuardConfig.from_yaml(path)
        assert config.custom_banned_expressions == ["snake oil"]
        Path(path).unlink()

    def test_load_locale_en(self):
        config = GuardConfig(locale="en")
        locale_data = config.load_locale()
        assert "banned_expressions" in locale_data
        assert "disclaimer_patterns" in locale_data

    def test_load_locale_ko(self):
        config = GuardConfig(locale="ko")
        locale_data = config.load_locale()
        assert "banned_expressions" in locale_data

    def test_fallback_locale(self):
        config = GuardConfig(locale="nonexistent")
        locale_data = config.load_locale()
        assert locale_data.get("locale") == "en"
