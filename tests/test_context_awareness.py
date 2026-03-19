"""Tests for context awareness check."""

from llm_medical_guard import Severity


class TestContextAwareness:
    def test_educational_content(self, guard_en):
        text = (
            "Studies show that vitamin D deficiency may increase the risk of "
            "certain conditions. According to clinical evidence, supplementation "
            "in some cases can help. Consult your healthcare provider."
        )
        result = guard_en.check(text)
        ctx = next(c for c in result.checks if c.check_name == "context_awareness")
        assert ctx.passed
        assert ctx.details.get("tone") == "educational"

    def test_fearmongering_content(self, guard_en):
        text = (
            "This deadly combination is a ticking time bomb! "
            "Big pharma doesn't want you to know this shocking truth. "
            "They are hiding the real cure. You're being lied to! "
            "Before it's too late, discover what they won't tell you."
        )
        result = guard_en.check(text)
        ctx = next(c for c in result.checks if c.check_name == "context_awareness")
        assert not ctx.passed
        assert ctx.details.get("tone") == "fearmongering"

    def test_promotional_content(self, guard_en):
        text = (
            "Buy now and get 50% off! Limited time offer on our health supplement. "
            "Use discount code HEALTH50. Free shipping on orders over $50. "
            "Click here to order today! Subscribe now for exclusive deals."
        )
        result = guard_en.check(text)
        ctx = next(c for c in result.checks if c.check_name == "context_awareness")
        assert not ctx.passed
        assert ctx.details.get("tone") == "promotional"

    def test_neutral_content(self, guard_en):
        text = "Vitamin D is a fat-soluble vitamin."
        result = guard_en.check(text)
        ctx = next(c for c in result.checks if c.check_name == "context_awareness")
        assert ctx.passed
        assert ctx.details.get("tone") == "neutral"

    def test_scores_in_details(self, guard_en):
        text = "Research shows this may cause side effects in rare cases."
        result = guard_en.check(text)
        ctx = next(c for c in result.checks if c.check_name == "context_awareness")
        assert "scores" in ctx.details
        assert "educational" in ctx.details["scores"]
