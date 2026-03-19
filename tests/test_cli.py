"""Tests for CLI."""

from llm_medical_guard.cli import main


class TestCLI:
    def test_check_safe(self):
        code = main([
            "check",
            "Vitamin D is good."
            " Not a substitute for professional"
            " medical advice. Source: NIH.",
        ])
        assert code == 0

    def test_check_dangerous(self):
        code = main(["check", "--strict", "This miracle cure has no side effects!"])
        assert code == 1

    def test_check_json_output(self, capsys):
        main(["check", "--json", "This miracle cure works!"])
        captured = capsys.readouterr()
        assert '"passed"' in captured.out
        assert '"checks"' in captured.out

    def test_check_locale(self):
        code = main([
            "check", "-l", "ko",
            "의사·약사의 전문적 판단을 대체하지 않습니다."
            " 식약처 DUR 기반.",
        ])
        assert code == 0

    def test_check_verbose(self, capsys):
        main(["check", "-v", "This miracle cure has no side effects!"])
        captured = capsys.readouterr()
        assert "→" in captured.out  # Shows suggestions

    def test_check_selective(self):
        code = main(["check", "--checks", "disclaimer", "--", "For informational purposes only."])
        assert code == 0

    def test_no_command(self):
        code = main([])
        assert code == 0

    def test_bench(self):
        code = main(["bench", "-n", "100"])
        assert code == 0
