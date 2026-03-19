"""Check for brand name mentions."""

from __future__ import annotations

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity

# Common pharmaceutical/supplement brand names
_DEFAULT_BRANDS_EN = [
    "Tylenol", "Advil", "Motrin", "Aleve", "Bayer",
    "Excedrin", "NyQuil", "DayQuil", "Mucinex", "Claritin",
    "Zyrtec", "Allegra", "Prilosec", "Nexium", "Tums",
    "Pepto-Bismol", "Imodium", "Centrum", "One A Day",
    "Nature Made", "GNC", "NOW Foods", "Solgar",
    "Garden of Life", "Nordic Naturals", "Kirkland",
]


@CheckRegistry.register
class BrandMentionCheck(BaseCheck):
    """Detects pharmaceutical and supplement brand name mentions."""

    name = "brand_mention"
    description = "Detects brand names that may indicate promotional content."

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        locale_data = config.load_locale()
        messages = locale_data.get("messages", {})

        brands = list(_DEFAULT_BRANDS_EN) + config.custom_brands
        found: list[str] = []

        for brand in brands:
            if brand.lower() in text.lower():
                found.append(brand)

        if not found:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="No brand names detected.",
            )

        brands_str = ", ".join(found[:5])
        suffix = f" (+{len(found) - 5} more)" if len(found) > 5 else ""

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.WARNING,
            severity=Severity.CAUTION,
            message=(
                f"{messages.get('brand_found', 'Brand names detected')}"
                f": {brands_str}{suffix}."
                " Consider using generic/ingredient names."
            ),
            details={
                "found_brands": found,
                "hint": "Use generic names (e.g., 'acetaminophen' instead of 'Tylenol').",
            },
        )
