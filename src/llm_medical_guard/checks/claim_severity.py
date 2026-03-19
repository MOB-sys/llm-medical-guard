"""Check for unsubstantiated medical claims."""

from __future__ import annotations

import re

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity


@CheckRegistry.register
class ClaimSeverityCheck(BaseCheck):
    """Detects unsubstantiated medical claims like treatment efficacy statements."""

    name = "claim_severity"
    description = "Detects treatment claims, prevention claims, and unqualified health statements."

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        locale_data = config.load_locale()
        patterns = locale_data.get("claim_patterns", [])
        messages = locale_data.get("messages", {})

        found: list[dict] = []

        for entry in patterns:
            pattern = entry["pattern"]
            severity = entry.get("severity", "warning")
            try:
                flags = re.IGNORECASE if config.locale == "en" else 0
                matches = list(re.finditer(pattern, text, flags))
            except re.error:
                continue

            for match in matches:
                found.append({
                    "claim": match.group(),
                    "severity": severity,
                    "position": match.start(),
                })

        if not found:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="No unsubstantiated claims found.",
            )

        max_severity = Severity.INFO
        for item in found:
            sev = Severity(item["severity"])
            if sev > max_severity:
                max_severity = sev

        claims_str = ", ".join(f"'{f['claim']}'" for f in found[:5])
        suffix = f" (+{len(found) - 5} more)" if len(found) > 5 else ""

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.FAIL if max_severity >= Severity.WARNING else CheckStatus.WARNING,
            severity=max_severity,
            message=f"{messages.get('claim_found', 'Medical claim detected')}: {claims_str}{suffix}",
            details={"found_claims": found},
        )
