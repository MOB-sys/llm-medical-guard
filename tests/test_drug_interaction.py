"""Tests for drug interaction check."""

from llm_medical_guard import Severity


class TestDrugInteraction:
    def test_warfarin_aspirin(self, guard_en):
        text = "You can safely take warfarin and aspirin together."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert not di.passed
        assert di.severity >= Severity.WARNING

    def test_warfarin_aspirin_with_warning(self, guard_en):
        text = (
            "Taking warfarin and aspirin together"
            " increases the risk of bleeding."
            " Consult your doctor."
        )
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        # Should still flag but with reduced severity since warning is present
        assert "has_warning" in str(di.details)

    def test_ssri_maoi(self, guard_en):
        text = "Combining fluoxetine with phenelzine can be beneficial."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert not di.passed
        assert di.severity == Severity.DANGER

    def test_statin_grapefruit(self, guard_en):
        text = "Enjoy grapefruit juice while taking atorvastatin."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert not di.passed

    def test_no_interaction(self, guard_en):
        text = "Vitamin D and vitamin C are both important for health."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert di.passed

    def test_thyroid_calcium(self, guard_en):
        text = "Take levothyroxine with your calcium supplement in the morning."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert not di.passed

    def test_st_johns_wort(self, guard_en):
        text = "St. John's Wort is great to take with your birth control pills."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert not di.passed
        assert di.severity == Severity.DANGER

    def test_iron_calcium_caution(self, guard_en):
        text = "I take calcium and iron supplements at the same time."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert not di.passed

    def test_antibiotic_dairy(self, guard_en):
        text = "Drink milk when taking doxycycline for better absorption."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert not di.passed

    def test_interaction_details(self, guard_en):
        text = "Warfarin and fish oil are a safe combination."
        result = guard_en.check(text)
        di = next(c for c in result.checks if c.check_name == "drug_interaction")
        assert "interactions" in di.details
        assert len(di.details["interactions"]) >= 1
        assert "source" in di.details["interactions"][0]
