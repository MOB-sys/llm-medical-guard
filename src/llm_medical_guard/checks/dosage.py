"""Check for dosage safety."""

from __future__ import annotations

import re

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity


@CheckRegistry.register
class DosageCheck(BaseCheck):
    """Validates dosage claims against known safe limits."""

    name = "dosage"
    description = "Detects dosage mentions and validates against known safe limits."

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        locale_data = config.load_locale()
        dosage_config = locale_data.get("dosage", {})
        units = dosage_config.get("units", ["mg", "mcg", "g", "IU"])
        known_limits = dosage_config.get("known_limits", {})
        messages = locale_data.get("messages", {})

        # Build unit pattern
        unit_pattern = "|".join(re.escape(u) for u in units)
        dosage_pattern = rf"(\d[\d,]*\.?\d*)\s*({unit_pattern})\b"

        issues: list[dict] = []
        text_lower = text.lower()

        for match in re.finditer(dosage_pattern, text, re.IGNORECASE):
            amount_str = match.group(1).replace(",", "")
            unit = match.group(2)
            try:
                amount = float(amount_str)
            except ValueError:
                continue

            # Check against known limits
            for _key, limits in known_limits.items():
                names = [n.lower() for n in limits.get("names", [])]
                limit_unit = limits.get("unit", "").lower()

                if unit.lower() != limit_unit:
                    continue

                # Check if any of the substance names appear near the dosage
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 50)
                context = text_lower[context_start:context_end]

                for name in names:
                    if name in context:
                        max_daily = limits.get("max_daily", float("inf"))
                        warning_threshold = limits.get("warning_threshold", float("inf"))

                        if amount >= warning_threshold:
                            issues.append({
                                "substance": name,
                                "amount": amount,
                                "unit": unit,
                                "max_daily": max_daily,
                                "severity": "danger",
                                "message": f"{name}: {amount}{unit} far exceeds max recommended {max_daily}{unit}/day",
                            })
                        elif amount > max_daily:
                            issues.append({
                                "substance": name,
                                "amount": amount,
                                "unit": unit,
                                "max_daily": max_daily,
                                "severity": "warning",
                                "message": f"{name}: {amount}{unit} exceeds max recommended {max_daily}{unit}/day",
                            })
                        break

        if not issues:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="No dosage issues detected.",
            )

        max_severity = Severity.INFO
        for issue in issues:
            sev = Severity(issue["severity"])
            if sev > max_severity:
                max_severity = sev

        msg_parts = [issue["message"] for issue in issues[:3]]
        suffix = f" (+{len(issues) - 3} more)" if len(issues) > 3 else ""

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.FAIL if max_severity >= Severity.WARNING else CheckStatus.WARNING,
            severity=max_severity,
            message=f"{messages.get('dosage_exceeded', 'Dosage issue')}: {'; '.join(msg_parts)}{suffix}",
            details={"issues": issues},
        )
