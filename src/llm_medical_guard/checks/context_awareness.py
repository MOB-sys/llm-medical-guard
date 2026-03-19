"""Context-aware medical content check — distinguishes education from fear-mongering."""

from __future__ import annotations

import re

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity

# Patterns that indicate educational/informational context
_EDUCATIONAL_PATTERNS = [
    r"(?:studies?|research|evidence) (?:show|suggest|indicate|found)",
    r"according to",
    r"risk (?:of|for|factor)",
    r"may (?:cause|lead to|result in|increase)",
    r"can (?:cause|lead to|result in)",
    r"in (?:some|rare|certain) cases",
    r"(?:clinical|medical) (?:studies?|trials?|evidence|literature)",
    r"(?:reported|observed|documented) (?:cases?|instances?|side effects?)",
    r"(?:healthcare|medical) (?:professional|provider|practitioner)",
    r"(?:peer[- ]reviewed|published)",
    r"(?:mechanism|pathway|pharmacokinetic)",
    r"(?:incidence|prevalence|rate) of",
]

# Patterns that indicate fear-mongering/sensationalism
_FEARMONGERING_PATTERNS = [
    r"(?:you |it )?(?:will|could|might) (?:die|kill you)",
    r"deadly",
    r"silent killer",
    r"ticking time bomb",
    r"poison(?:ing|ous)?",
    r"toxic (?:cocktail|combination|mix)",
    r"destroying your",
    r"ruining your",
    r"doctors? (?:are |have been )?hiding",
    r"(?:big )?pharma (?:doesn'?t|won'?t|doesn't)",
    r"they don'?t want you to know",
    r"shocking (?:truth|secret|discovery)",
    r"what (?:they|doctors?) (?:won'?t|don'?t) tell you",
    r"before it'?s too late",
    r"you'?re being (?:lied to|deceived|poisoned)",
]

# Patterns indicating promotional/sales content
_PROMOTIONAL_PATTERNS = [
    r"buy (?:now|today|this)",
    r"order (?:now|today|yours)",
    r"limited (?:time|offer|supply)",
    r"(?:use |with )?(?:discount|coupon|promo) code",
    r"(?:\$|USD |€)\d+",
    r"free (?:shipping|trial|sample)",
    r"subscribe (?:now|today)",
    r"click (?:here|the link|below)",
    r"affiliate",
    r"sponsored",
]


@CheckRegistry.register
class ContextAwarenessCheck(BaseCheck):
    """Analyzes the overall tone and context of medical content."""

    name = "context_awareness"
    description = (
        "Distinguishes educational medical content"
        " from fear-mongering or promotional content."
    )

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        text_lower = text.lower()

        edu_score = 0
        fear_score = 0
        promo_score = 0
        details: dict = {
            "educational_signals": [],
            "fearmongering_signals": [],
            "promotional_signals": [],
        }

        for pattern in _EDUCATIONAL_PATTERNS:
            matches = re.findall(pattern, text_lower)
            if matches:
                edu_score += len(matches)
                details["educational_signals"].append(matches[0])

        for pattern in _FEARMONGERING_PATTERNS:
            matches = re.findall(pattern, text_lower)
            if matches:
                fear_score += len(matches) * 2  # Weight fear signals higher
                details["fearmongering_signals"].append(matches[0])

        for pattern in _PROMOTIONAL_PATTERNS:
            matches = re.findall(pattern, text_lower)
            if matches:
                promo_score += len(matches) * 2
                details["promotional_signals"].append(matches[0])

        total_signals = edu_score + fear_score + promo_score
        if total_signals == 0:
            # Neutral content — no strong signals either way
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="Content tone is neutral.",
                details={
                    "tone": "neutral",
                    "scores": {
                        "educational": 0,
                        "fearmongering": 0,
                        "promotional": 0,
                    },
                },
            )

        details["scores"] = {
            "educational": edu_score,
            "fearmongering": fear_score,
            "promotional": promo_score,
        }

        # Determine dominant tone
        if fear_score > edu_score and fear_score >= 4:
            details["tone"] = "fearmongering"
            signals_str = ", ".join(f"'{s}'" for s in details["fearmongering_signals"][:3])
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.FAIL,
                severity=Severity.WARNING,
                message=f"Content appears to use fear-mongering tone: {signals_str}",
                details=details,
            )

        if promo_score > edu_score and promo_score >= 4:
            details["tone"] = "promotional"
            signals_str = ", ".join(f"'{s}'" for s in details["promotional_signals"][:3])
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.FAIL,
                severity=Severity.WARNING,
                message=f"Content appears promotional/sales-oriented: {signals_str}",
                details=details,
            )

        if edu_score >= fear_score and edu_score >= promo_score:
            details["tone"] = "educational"
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="Content tone is educational/informational.",
                details=details,
            )

        # Mixed signals
        details["tone"] = "mixed"
        return CheckResult(
            check_name=self.name,
            status=CheckStatus.WARNING,
            severity=Severity.CAUTION,
            message="Content has mixed signals — review for tone consistency.",
            details=details,
        )
