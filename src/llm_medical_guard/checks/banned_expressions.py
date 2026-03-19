"""Check for banned/prohibited medical expressions."""

from __future__ import annotations

import re

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity


@CheckRegistry.register
class BannedExpressionsCheck(BaseCheck):
    """Detects banned medical expressions and suggests safe alternatives."""

    name = "banned_expressions"
    description = "Detects prohibited medical expressions like cure claims, fear-mongering, etc."

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        locale_data = config.load_locale()
        banned = locale_data.get("banned_expressions", [])
        messages = locale_data.get("messages", {})

        found: list[dict] = []
        text_lower = text.lower()

        for entry in banned:
            pattern = entry["pattern"]
            try:
                flags = re.IGNORECASE if config.locale == "en" else 0
                matches = list(re.finditer(pattern, text if not flags else text_lower, flags))
            except re.error:
                # Fallback to substring match
                if pattern.lower() in text_lower:
                    matches = [True]  # type: ignore[list-item]
                else:
                    matches = []

            if matches:
                # Use the actual matched text instead of raw regex pattern
                if isinstance(matches[0], bool):
                    matched_text = pattern
                else:
                    matched_text = matches[0].group()
                found.append({
                    "expression": matched_text,
                    "category": entry.get("category", "unknown"),
                    "severity": entry.get("severity", "warning"),
                    "suggestion": entry.get("suggestion", ""),
                    "count": len(matches),
                })

        # Also check custom banned expressions
        for expr in config.custom_banned_expressions:
            if expr.lower() in text_lower:
                suggestion = config.custom_safe_alternatives.get(expr, "")
                found.append({
                    "expression": expr,
                    "category": "custom",
                    "severity": "warning",
                    "suggestion": suggestion,
                    "count": 1,
                })

        if not found:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="No banned expressions found.",
            )

        max_severity = Severity.INFO
        for item in found:
            sev = Severity(item["severity"])
            if sev > max_severity:
                max_severity = sev

        expressions_str = ", ".join(f"'{f['expression']}'" for f in found[:5])
        suffix = f" (+{len(found) - 5} more)" if len(found) > 5 else ""

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.FAIL if max_severity >= Severity.WARNING else CheckStatus.WARNING,
            severity=max_severity,
            message=(
                f"{messages.get('banned_found', 'Banned expression detected')}"
                f": {expressions_str}{suffix}"
            ),
            details={
                "found": found,
                "suggestions": {f["expression"]: f["suggestion"] for f in found if f["suggestion"]},
            },
        )
