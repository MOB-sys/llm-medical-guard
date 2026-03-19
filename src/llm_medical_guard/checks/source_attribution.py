"""Check for source/citation attribution."""

from __future__ import annotations

import re

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity


@CheckRegistry.register
class SourceAttributionCheck(BaseCheck):
    """Checks that medical content cites authoritative sources."""

    name = "source_attribution"
    description = "Verifies that authoritative medical sources are cited."

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        locale_data = config.load_locale()
        valid_sources = locale_data.get("valid_sources", [])
        messages = locale_data.get("messages", {})

        found_sources: list[str] = []
        text_lower = text.lower()

        for source in valid_sources:
            if source.lower() in text_lower:
                found_sources.append(source)

        # Also check for URL patterns (common citation format)
        url_pattern = r"https?://[\w\-._~:/?#\[\]@!$&\'()*+,;=%]+"
        urls = re.findall(url_pattern, text)

        if found_sources:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message=f"Source attribution found: {', '.join(found_sources[:3])}",
                details={"sources": found_sources, "urls": urls},
            )

        if urls:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.WARNING,
                severity=Severity.CAUTION,
                message="URLs found but no recognized authoritative medical source.",
                details={"sources": [], "urls": urls},
            )

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.FAIL,
            severity=Severity.WARNING,
            message=messages.get("source_missing", "No authoritative source cited."),
            details={
                "expected_sources": valid_sources[:5],
                "hint": "Cite an authoritative source such as FDA, NIH, or peer-reviewed studies.",
            },
        )
