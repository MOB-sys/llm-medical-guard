"""Tests for badge generation."""

import os
import tempfile

from llm_medical_guard.badge import generate_badge


class TestBadge:
    def test_pass_badge(self, guard_en):
        result = guard_en.check(
            "Vitamin D supports health."
            " Not a substitute for professional"
            " medical advice. Source: NIH."
        )
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            path = f.name
        try:
            svg = generate_badge(result, path)
            assert "<svg" in svg
            assert "passed" in svg
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_fail_badge(self, guard_en):
        result = guard_en.check("This miracle cure has no side effects!")
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            path = f.name
        try:
            svg = generate_badge(result, path)
            assert "<svg" in svg
            assert "danger" in svg.lower() or "warning" in svg.lower()
        finally:
            os.unlink(path)
