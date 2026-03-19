"""Result types for medical guard checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Severity level of a medical content issue."""

    DANGER = "danger"
    WARNING = "warning"
    CAUTION = "caution"
    INFO = "info"

    def __ge__(self, other: Severity) -> bool:
        order = {Severity.INFO: 0, Severity.CAUTION: 1, Severity.WARNING: 2, Severity.DANGER: 3}
        return order[self] >= order[other]

    def __gt__(self, other: Severity) -> bool:
        order = {Severity.INFO: 0, Severity.CAUTION: 1, Severity.WARNING: 2, Severity.DANGER: 3}
        return order[self] > order[other]

    def __le__(self, other: Severity) -> bool:
        return not self.__gt__(other)

    def __lt__(self, other: Severity) -> bool:
        return not self.__ge__(other)


class CheckStatus(Enum):
    """Status of an individual check."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class CheckResult:
    """Result of a single guard check."""

    check_name: str
    status: CheckStatus
    severity: Severity
    message: str
    details: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASS


@dataclass
class GuardResult:
    """Aggregated result of all guard checks."""

    passed: bool
    score: float
    severity: Severity
    checks: list[CheckResult]
    text: str

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    @property
    def summary(self) -> str:
        if self.passed:
            return f"All {len(self.checks)} checks passed."
        failures = self.failed_checks
        lines = [f"{len(failures)}/{len(self.checks)} checks failed:"]
        for f in failures:
            lines.append(f"  - [{f.severity.value.upper()}] {f.check_name}: {f.message}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "score": round(self.score, 2),
            "severity": self.severity.value,
            "summary": self.summary,
            "checks": [
                {
                    "check_name": c.check_name,
                    "status": c.status.value,
                    "severity": c.severity.value,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.checks
            ],
        }

    def raise_on_fail(self) -> None:
        if not self.passed:
            raise MedicalGuardError(self.summary, result=self)


class MedicalGuardError(Exception):
    """Raised when medical content fails guard checks."""

    def __init__(self, message: str, result: GuardResult | None = None):
        super().__init__(message)
        self.result = result
