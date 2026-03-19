"""Tests for brand mention check."""

from llm_medical_guard import MedicalGuard


class TestBrandMention:
    def test_brand_detected(self, guard_en):
        text = "Take Tylenol for headaches."
        result = guard_en.check(text)
        brand = next(c for c in result.checks if c.check_name == "brand_mention")
        assert not brand.passed
        assert "Tylenol" in brand.details["found_brands"]

    def test_no_brand(self, guard_en):
        text = "Acetaminophen can help with headaches."
        result = guard_en.check(text)
        brand = next(c for c in result.checks if c.check_name == "brand_mention")
        assert brand.passed

    def test_multiple_brands(self, guard_en):
        text = "Don't mix Tylenol and Advil together."
        result = guard_en.check(text)
        brand = next(c for c in result.checks if c.check_name == "brand_mention")
        assert len(brand.details["found_brands"]) >= 2

    def test_custom_brand(self):
        guard = MedicalGuard(config={"custom_brands": ["HealthMax"]})
        result = guard.check("Try HealthMax supplements.")
        brand = next(c for c in result.checks if c.check_name == "brand_mention")
        assert not brand.passed
