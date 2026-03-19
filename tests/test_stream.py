"""Tests for streaming support."""

from llm_medical_guard import MedicalGuard
from llm_medical_guard.stream import StreamGuard, check_stream


class TestStreamGuard:
    def test_feed_safe_content(self):
        sg = StreamGuard(locale="en")
        alert = sg.feed("Vitamin D is important for bone health. ")
        assert alert is None  # Not enough chars to trigger check

    def test_feed_triggers_check(self):
        sg = StreamGuard(locale="en", check_interval=50)
        # Feed enough text to trigger a check
        alert = sg.feed("This miracle cure " * 10)
        assert alert is not None
        assert not alert.passed

    def test_finalize(self):
        sg = StreamGuard(locale="en")
        sg.feed("This is safe content. ")
        sg.feed("Consult your doctor. ")
        sg.feed("Source: NIH. ")
        sg.feed("Not a substitute for professional medical advice.")
        result = sg.finalize()
        assert result.passed

    def test_finalize_with_issues(self):
        sg = StreamGuard(locale="en")
        sg.feed("This miracle cure has no side effects!")
        result = sg.finalize()
        assert not result.passed

    def test_reset(self):
        sg = StreamGuard(locale="en")
        sg.feed("Some text")
        sg.reset()
        assert sg.text == ""
        assert sg.last_result is None

    def test_text_accumulation(self):
        sg = StreamGuard(locale="en")
        sg.feed("Hello ")
        sg.feed("world")
        assert sg.text == "Hello world"

    def test_custom_guard(self):
        guard = MedicalGuard(locale="ko")
        sg = StreamGuard(guard=guard)
        sg.feed("만병통치약입니다!")
        result = sg.finalize()
        assert not result.passed


class TestCheckStream:
    def test_generator(self):
        chunks = ["Hello ", "this is ", "safe content. ", "Source: NIH. ",
                   "Not a substitute for professional medical advice."]
        results = list(check_stream(chunks, check_interval=1000))
        assert len(results) == len(chunks)
        # All should be (chunk, None) since interval is high
        for chunk, alert in results:
            assert isinstance(chunk, str)

    def test_catches_issues(self):
        chunks = ["This miracle cure "] * 20
        alerts_found = False
        for chunk, alert in check_stream(chunks, check_interval=50):
            if alert is not None:
                alerts_found = True
                assert not alert.passed
        assert alerts_found
