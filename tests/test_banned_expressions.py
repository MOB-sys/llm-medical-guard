"""Tests for banned expressions check."""

from llm_medical_guard import MedicalGuard, Severity


class TestBannedExpressions:
    def test_cure_claim(self, guard_en):
        result = guard_en.check("This herb cures diabetes completely.")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert not banned.passed
        assert banned.severity == Severity.DANGER

    def test_miracle_cure(self, guard_en):
        result = guard_en.check("Try this miracle cure for weight loss!")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert not banned.passed

    def test_safe_content(self, guard_en):
        result = guard_en.check("Vitamin D supports bone health when taken as recommended.")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert banned.passed

    def test_anti_professional(self, guard_en):
        result = guard_en.check("This is better than your doctor's advice!")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert not banned.passed
        assert banned.severity == Severity.DANGER

    def test_absolute_safety(self, guard_en):
        result = guard_en.check("This supplement is 100% safe with no side effects.")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert not banned.passed

    def test_suggestions_provided(self, guard_en):
        result = guard_en.check("This miracle cure works instantly!")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert "suggestions" in banned.details
        assert len(banned.details["suggestions"]) > 0

    def test_fear_mongering(self, guard_en):
        result = guard_en.check("Taking these together could kill you!")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert not banned.passed
        assert banned.severity == Severity.DANGER

    def test_korean_banned(self, guard_ko):
        result = guard_ko.check("이것만 먹으면 완치됩니다!")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert not banned.passed
        assert banned.severity == Severity.DANGER

    def test_custom_banned(self):
        guard = MedicalGuard(config={"custom_banned_expressions": ["detox cleanse"]})
        result = guard.check("Try our detox cleanse program!")
        banned = next(c for c in result.checks if c.check_name == "banned_expressions")
        assert not banned.passed
