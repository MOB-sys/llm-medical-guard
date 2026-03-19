"""Integration tests for MedicalGuard."""

import pytest

from llm_medical_guard import MedicalGuard, MedicalGuardError, Severity


class TestMedicalGuard:
    def test_safe_content_passes(self, guard_en):
        text = (
            "Vitamin D may help support bone health when taken as directed. "
            "Consult your doctor before starting any supplement. "
            "Source: NIH Office of Dietary Supplements. "
            "This is not a substitute for professional medical advice."
        )
        result = guard_en.check(text)
        assert result.passed
        assert result.score == 1.0
        assert result.severity == Severity.INFO

    def test_dangerous_content_fails(self, guard_en):
        text = "This miracle cure will instantly cure your cancer with zero risk and no side effects."
        result = guard_en.check(text)
        assert not result.passed
        assert result.severity == Severity.DANGER
        assert len(result.failed_checks) > 0

    def test_summary_format(self, guard_en):
        text = "Take this miracle cure now! 100% safe!"
        result = guard_en.check(text)
        summary = result.summary
        assert "checks failed" in summary
        assert "DANGER" in summary or "WARNING" in summary

    def test_to_dict(self, guard_en):
        text = "Vitamin C is generally safe. Consult your doctor. Source: NIH."
        result = guard_en.check(text)
        d = result.to_dict()
        assert "passed" in d
        assert "score" in d
        assert "checks" in d
        assert isinstance(d["checks"], list)

    def test_strict_mode_raises(self, strict_guard):
        text = "This miracle cure has no side effects!"
        with pytest.raises(MedicalGuardError):
            strict_guard.check(text)

    def test_check_or_raise_passes(self, guard_en):
        text = (
            "Omega-3 fatty acids may support heart health. "
            "This is not a substitute for professional medical advice. "
            "Source: FDA."
        )
        returned = guard_en.check_or_raise(text)
        assert returned == text

    def test_check_or_raise_fails(self, guard_en):
        text = "This cures all diseases instantly!"
        with pytest.raises(MedicalGuardError):
            guard_en.check_or_raise(text)

    def test_selective_checks(self):
        guard = MedicalGuard(checks=["banned_expressions", "disclaimer"])
        text = "This is a test without any issues. For informational purposes only."
        result = guard.check(text)
        assert len(result.checks) == 2

    def test_custom_config_dict(self):
        guard = MedicalGuard(
            config={"custom_banned_expressions": ["super juice"]},
            locale="en",
        )
        result = guard.check("Try our super juice for health!")
        failed_names = [c.check_name for c in result.failed_checks]
        assert "banned_expressions" in failed_names


class TestKoreanGuard:
    def test_korean_banned_expression(self, guard_ko):
        text = "이 약을 먹으면 암 예방이 됩니다. 만병통치약입니다!"
        result = guard_ko.check(text)
        assert not result.passed
        assert result.severity == Severity.DANGER

    def test_korean_safe_content(self, guard_ko):
        text = (
            "비타민D는 뼈 건강에 도움이 될 수 있습니다. "
            "의사·약사의 전문적 판단을 대체하지 않습니다. "
            "식약처 DUR 데이터 기반."
        )
        result = guard_ko.check(text)
        assert result.passed

    def test_korean_disclaimer_check(self, guard_ko):
        text = "비타민C를 매일 드세요!"
        result = guard_ko.check(text)
        disclaimer_check = next(c for c in result.checks if c.check_name == "disclaimer")
        assert not disclaimer_check.passed


class TestJapaneseGuard:
    def test_japanese_banned_expression(self, guard_ja):
        text = "この薬は万能薬です。完治します。"
        result = guard_ja.check(text)
        assert not result.passed
        assert result.severity == Severity.DANGER

    def test_japanese_safe_content(self, guard_ja):
        text = (
            "ビタミンDは骨の健康をサポートする可能性があります。"
            "情報提供を目的としています。"
            "厚生労働省のデータに基づいています。"
        )
        result = guard_ja.check(text)
        assert result.passed
