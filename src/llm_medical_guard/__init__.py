"""llm-medical-guard: Guardrails for LLM-generated medical content."""

from llm_medical_guard.guard import MedicalGuard
from llm_medical_guard.result import (
    CheckResult,
    CheckStatus,
    GuardResult,
    MedicalGuardError,
    Severity,
)

__version__ = "0.1.0"

__all__ = [
    "MedicalGuard",
    "GuardResult",
    "CheckResult",
    "CheckStatus",
    "Severity",
    "MedicalGuardError",
    "__version__",
]
