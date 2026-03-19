"""Tests for disclaimer check."""

from llm_medical_guard import Severity


class TestDisclaimer:
    def test_has_disclaimer(self, guard_en):
        text = "Omega-3 is beneficial. This is not a substitute for professional medical advice."
        result = guard_en.check(text)
        disc = next(c for c in result.checks if c.check_name == "disclaimer")
        assert disc.passed

    def test_missing_disclaimer(self, guard_en):
        text = "Take vitamin D every day for strong bones."
        result = guard_en.check(text)
        disc = next(c for c in result.checks if c.check_name == "disclaimer")
        assert not disc.passed
        assert disc.severity == Severity.WARNING

    def test_alternative_disclaimer(self, guard_en):
        text = "Zinc supports immunity. For informational purposes only."
        result = guard_en.check(text)
        disc = next(c for c in result.checks if c.check_name == "disclaimer")
        assert disc.passed

    def test_consult_doctor_disclaimer(self, guard_en):
        text = "Please consult your healthcare provider before use."
        result = guard_en.check(text)
        disc = next(c for c in result.checks if c.check_name == "disclaimer")
        assert disc.passed

    def test_korean_disclaimer(self, guard_ko):
        text = "본 정보는 의사·약사의 전문적 판단을 대체하지 않습니다."
        result = guard_ko.check(text)
        disc = next(c for c in result.checks if c.check_name == "disclaimer")
        assert disc.passed

    def test_japanese_disclaimer(self, guard_ja):
        text = "この情報は情報提供を目的としています。"
        result = guard_ja.check(text)
        disc = next(c for c in result.checks if c.check_name == "disclaimer")
        assert disc.passed
