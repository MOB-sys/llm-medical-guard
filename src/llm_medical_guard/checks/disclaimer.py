"""Check for required medical disclaimers."""

from __future__ import annotations

import re

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity


@CheckRegistry.register
class DisclaimerCheck(BaseCheck):
    """Verifies that required medical disclaimers are present."""

    name = "disclaimer"
    description = "Checks for the presence of required medical disclaimers."

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        locale_data = config.load_locale()
        patterns = locale_data.get("disclaimer_patterns", [])
        messages = locale_data.get("messages", {})

        # Add custom patterns
        all_patterns = patterns + config.custom_disclaimer_patterns

        for pattern in all_patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return CheckResult(
                        check_name=self.name,
                        status=CheckStatus.PASS,
                        severity=Severity.INFO,
                        message="Medical disclaimer found.",
                        details={"matched_pattern": pattern},
                    )
            except re.error:
                if pattern.lower() in text.lower():
                    return CheckResult(
                        check_name=self.name,
                        status=CheckStatus.PASS,
                        severity=Severity.INFO,
                        message="Medical disclaimer found.",
                        details={"matched_pattern": pattern},
                    )

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.FAIL,
            severity=Severity.WARNING,
            message=messages.get("disclaimer_missing", "Required medical disclaimer not found."),
            details={
                "expected_patterns": all_patterns[:3],
                "hint": (
                    "Add a disclaimer such as:"
                    " 'This is not a substitute for"
                    " professional medical advice.'"
                ),
            },
        )
