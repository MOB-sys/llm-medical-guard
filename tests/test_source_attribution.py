"""Tests for source attribution check."""



class TestSourceAttribution:
    def test_has_source(self, guard_en):
        text = "According to FDA guidelines, this is safe."
        result = guard_en.check(text)
        src = next(c for c in result.checks if c.check_name == "source_attribution")
        assert src.passed

    def test_no_source(self, guard_en):
        text = "This supplement boosts your immunity significantly."
        result = guard_en.check(text)
        src = next(c for c in result.checks if c.check_name == "source_attribution")
        assert not src.passed

    def test_multiple_sources(self, guard_en):
        text = "Based on NIH and WHO data, vitamin D is essential."
        result = guard_en.check(text)
        src = next(c for c in result.checks if c.check_name == "source_attribution")
        assert src.passed
        assert len(src.details["sources"]) >= 2

    def test_url_only(self, guard_en):
        text = "Learn more at https://example.com/study"
        result = guard_en.check(text)
        src = next(c for c in result.checks if c.check_name == "source_attribution")
        assert src.status.value == "warning"

    def test_korean_source(self, guard_ko):
        text = "식약처 DUR 데이터에 따르면 이 조합은 주의가 필요합니다."
        result = guard_ko.check(text)
        src = next(c for c in result.checks if c.check_name == "source_attribution")
        assert src.passed

    def test_japanese_source(self, guard_ja):
        text = "厚生労働省のガイドラインに基づいています。"
        result = guard_ja.check(text)
        src = next(c for c in result.checks if c.check_name == "source_attribution")
        assert src.passed
