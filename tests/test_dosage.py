"""Tests for dosage check."""

from llm_medical_guard import Severity


class TestDosage:
    def test_safe_dosage(self, guard_en):
        text = "Take 1000 IU of vitamin D daily."
        result = guard_en.check(text)
        dosage = next(c for c in result.checks if c.check_name == "dosage")
        assert dosage.passed

    def test_excessive_dosage_warning(self, guard_en):
        text = "Take 5000 IU of vitamin D daily for best results."
        result = guard_en.check(text)
        dosage = next(c for c in result.checks if c.check_name == "dosage")
        assert not dosage.passed
        assert dosage.severity == Severity.WARNING

    def test_dangerous_dosage(self, guard_en):
        text = "Take 50000 IU of vitamin D every day."
        result = guard_en.check(text)
        dosage = next(c for c in result.checks if c.check_name == "dosage")
        assert not dosage.passed
        assert dosage.severity == Severity.DANGER

    def test_vitamin_c_excessive(self, guard_en):
        text = "I recommend 10000 mg of vitamin C for immunity."
        result = guard_en.check(text)
        dosage = next(c for c in result.checks if c.check_name == "dosage")
        assert not dosage.passed

    def test_iron_excessive(self, guard_en):
        text = "Take 200 mg of iron supplements daily."
        result = guard_en.check(text)
        dosage = next(c for c in result.checks if c.check_name == "dosage")
        assert not dosage.passed
        assert dosage.severity == Severity.DANGER

    def test_no_dosage_mentioned(self, guard_en):
        text = "Vitamin D is important for bone health."
        result = guard_en.check(text)
        dosage = next(c for c in result.checks if c.check_name == "dosage")
        assert dosage.passed

    def test_safe_melatonin(self, guard_en):
        text = "Try 3 mg of melatonin before bed."
        result = guard_en.check(text)
        dosage = next(c for c in result.checks if c.check_name == "dosage")
        assert dosage.passed

    def test_excessive_melatonin(self, guard_en):
        text = "Take 30 mg of melatonin for deep sleep."
        result = guard_en.check(text)
        dosage = next(c for c in result.checks if c.check_name == "dosage")
        assert not dosage.passed
