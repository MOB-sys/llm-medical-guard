"""Main MedicalGuard class — the primary entry point."""

from __future__ import annotations

from pathlib import Path

# Import checks to trigger registration
import llm_medical_guard.checks.banned_expressions  # noqa: F401
import llm_medical_guard.checks.brand_mention  # noqa: F401
import llm_medical_guard.checks.claim_severity  # noqa: F401
import llm_medical_guard.checks.context_awareness  # noqa: F401
import llm_medical_guard.checks.disclaimer  # noqa: F401
import llm_medical_guard.checks.dosage  # noqa: F401
import llm_medical_guard.checks.drug_interaction  # noqa: F401
import llm_medical_guard.checks.source_attribution  # noqa: F401
from llm_medical_guard.checks import CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckStatus, GuardResult, Severity


class MedicalGuard:
    """Validate LLM-generated medical/health content for safety.

    Usage:
        guard = MedicalGuard()
        result = guard.check("Take 10000 IU of vitamin D daily to cure depression")
        if not result.passed:
            print(result.summary)
    """

    def __init__(
        self,
        config: str | Path | dict | None = None,
        locale: str = "en",
        checks: list[str] | None = None,
        strict: bool = False,
    ):
        if isinstance(config, dict):
            self._config = GuardConfig.from_dict(config)
        elif isinstance(config, (str, Path)):
            self._config = GuardConfig.from_yaml(config)
        else:
            self._config = GuardConfig()

        # Override with explicit parameters
        self._config.locale = locale
        self._config.strict = strict
        if checks:
            self._config.checks_enabled = {
                name: (name in checks)
                for name in CheckRegistry.get_all()
            }

    @property
    def config(self) -> GuardConfig:
        return self._config

    def check(self, text: str) -> GuardResult:
        """Run all enabled checks on the given text.

        Args:
            text: The LLM-generated medical content to validate.

        Returns:
            GuardResult with pass/fail status, severity, and detailed check results.
        """
        enabled_checks = CheckRegistry.get_enabled(self._config)
        results = []

        for check in enabled_checks:
            result = check.run(text, self._config)
            results.append(result)

        # Compute aggregate
        passed_count = sum(1 for r in results if r.passed)
        total = len(results)
        score = passed_count / total if total > 0 else 1.0

        has_fail = any(r.status == CheckStatus.FAIL for r in results)
        max_severity = Severity.INFO
        for r in results:
            if r.severity > max_severity:
                max_severity = r.severity

        guard_result = GuardResult(
            passed=not has_fail,
            score=score,
            severity=max_severity,
            checks=results,
            text=text,
        )

        if self._config.strict and not guard_result.passed:
            guard_result.raise_on_fail()

        return guard_result

    def check_or_raise(self, text: str) -> str:
        """Check text and raise MedicalGuardError if it fails.

        Returns the original text if all checks pass.
        """
        result = self.check(text)
        result.raise_on_fail()
        return text
