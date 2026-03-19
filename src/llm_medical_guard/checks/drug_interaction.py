"""Check for known drug-drug and drug-supplement interactions."""

from __future__ import annotations

import re

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity

# Well-documented dangerous interactions (evidence-based, publicly available)
# Source: FDA drug labels, DailyMed, established medical literature
_KNOWN_INTERACTIONS: list[dict] = [
    # Blood thinners + NSAIDs
    {
        "drug_a": ["warfarin", "coumadin"],
        "drug_b": ["aspirin", "ibuprofen", "naproxen", "advil", "motrin", "aleve", "nsaid"],
        "severity": "danger",
        "description": "Increased risk of serious bleeding. NSAIDs inhibit platelet function and may displace warfarin from protein binding.",
        "source": "FDA Drug Label",
    },
    # ACE inhibitors + Potassium
    {
        "drug_a": ["lisinopril", "enalapril", "ramipril", "ace inhibitor"],
        "drug_b": ["potassium", "potassium chloride", "potassium supplement"],
        "severity": "warning",
        "description": "Risk of hyperkalemia (dangerously high potassium levels).",
        "source": "FDA Drug Label",
    },
    # SSRIs + MAOIs
    {
        "drug_a": ["fluoxetine", "sertraline", "paroxetine", "citalopram", "escitalopram", "ssri"],
        "drug_b": ["phenelzine", "tranylcypromine", "isocarboxazid", "selegiline", "maoi"],
        "severity": "danger",
        "description": "Risk of serotonin syndrome, a potentially life-threatening condition.",
        "source": "FDA Drug Safety Communication",
    },
    # Statins + Grapefruit
    {
        "drug_a": ["atorvastatin", "simvastatin", "lovastatin", "statin"],
        "drug_b": ["grapefruit", "grapefruit juice"],
        "severity": "warning",
        "description": "Grapefruit inhibits CYP3A4 enzyme, increasing statin blood levels and risk of muscle damage (rhabdomyolysis).",
        "source": "FDA Consumer Update",
    },
    # Metformin + Alcohol
    {
        "drug_a": ["metformin", "glucophage"],
        "drug_b": ["alcohol", "ethanol"],
        "severity": "warning",
        "description": "Increased risk of lactic acidosis, especially with heavy alcohol use.",
        "source": "FDA Drug Label",
    },
    # Blood thinners + Vitamin K
    {
        "drug_a": ["warfarin", "coumadin"],
        "drug_b": ["vitamin k", "phytonadione"],
        "severity": "warning",
        "description": "Vitamin K counteracts warfarin's anticoagulant effect, potentially leading to blood clots.",
        "source": "NIH Office of Dietary Supplements",
    },
    # Blood thinners + Fish oil
    {
        "drug_a": ["warfarin", "coumadin", "aspirin", "clopidogrel", "plavix"],
        "drug_b": ["fish oil", "omega-3", "omega 3", "epa", "dha"],
        "severity": "caution",
        "description": "May increase bleeding risk due to additive antiplatelet effects.",
        "source": "NIH / Natural Medicines Database",
    },
    # Thyroid medication + Calcium/Iron
    {
        "drug_a": ["levothyroxine", "synthroid", "thyroid medication"],
        "drug_b": ["calcium", "iron", "calcium carbonate", "ferrous sulfate"],
        "severity": "warning",
        "description": "Calcium and iron reduce absorption of thyroid medication. Take at least 4 hours apart.",
        "source": "American Thyroid Association",
    },
    # Antibiotics + Dairy
    {
        "drug_a": ["tetracycline", "doxycycline", "ciprofloxacin", "levofloxacin"],
        "drug_b": ["calcium", "dairy", "milk", "antacid"],
        "severity": "warning",
        "description": "Calcium-containing products reduce antibiotic absorption significantly.",
        "source": "FDA Drug Label",
    },
    # St. John's Wort interactions
    {
        "drug_a": ["st. john's wort", "st john's wort", "hypericum"],
        "drug_b": ["birth control", "oral contraceptive", "contraceptive", "ssri", "fluoxetine",
                    "sertraline", "warfarin", "cyclosporine", "digoxin"],
        "severity": "danger",
        "description": "St. John's Wort induces CYP450 enzymes, reducing effectiveness of many medications.",
        "source": "NIH NCCIH",
    },
    # Calcium + Iron (absorption competition)
    {
        "drug_a": ["calcium", "calcium carbonate", "calcium citrate"],
        "drug_b": ["iron", "ferrous sulfate", "ferrous gluconate"],
        "severity": "caution",
        "description": "Calcium inhibits iron absorption. Take at different times of day.",
        "source": "NIH Office of Dietary Supplements",
    },
    # Vitamin E + Blood thinners
    {
        "drug_a": ["vitamin e", "tocopherol"],
        "drug_b": ["warfarin", "aspirin", "clopidogrel", "blood thinner"],
        "severity": "caution",
        "description": "High-dose Vitamin E may increase bleeding risk with anticoagulants.",
        "source": "NIH Office of Dietary Supplements",
    },
    # Ginkgo + Blood thinners
    {
        "drug_a": ["ginkgo", "ginkgo biloba"],
        "drug_b": ["warfarin", "aspirin", "ibuprofen", "blood thinner", "anticoagulant"],
        "severity": "warning",
        "description": "Ginkgo has antiplatelet properties and may increase bleeding risk.",
        "source": "NCCIH / Natural Medicines Database",
    },
    # Magnesium + Antibiotics
    {
        "drug_a": ["magnesium", "magnesium oxide", "magnesium citrate"],
        "drug_b": ["tetracycline", "doxycycline", "ciprofloxacin", "levofloxacin"],
        "severity": "warning",
        "description": "Magnesium reduces absorption of certain antibiotics. Separate by 2-4 hours.",
        "source": "FDA Drug Label",
    },
    # Zinc + Copper
    {
        "drug_a": ["zinc"],
        "drug_b": ["copper"],
        "severity": "caution",
        "description": "High-dose zinc can cause copper deficiency over time.",
        "source": "NIH Office of Dietary Supplements",
    },
]


@CheckRegistry.register
class DrugInteractionCheck(BaseCheck):
    """Detects mentions of known dangerous drug-drug or drug-supplement interactions."""

    name = "drug_interaction"
    description = "Flags text that mentions known dangerous drug/supplement combinations without adequate warnings."

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        text_lower = text.lower()
        found_interactions: list[dict] = []

        for interaction in _KNOWN_INTERACTIONS:
            a_names = interaction["drug_a"]
            b_names = interaction["drug_b"]

            a_found = any(name in text_lower for name in a_names)
            b_found = any(name in text_lower for name in b_names)

            if a_found and b_found:
                # Check if there's already a warning/caution in the text
                has_warning = any(
                    w in text_lower
                    for w in [
                        "risk", "danger", "caution", "warning", "avoid",
                        "do not", "don't", "should not", "consult",
                        "위험", "주의", "금지", "피하", "상담",
                        "リスク", "危険", "注意", "避け",
                    ]
                )

                # If the text already warns about the interaction, reduce severity
                effective_severity = interaction["severity"]
                if has_warning and effective_severity == "danger":
                    effective_severity = "warning"
                elif has_warning and effective_severity == "warning":
                    effective_severity = "caution"

                a_match = next(n for n in a_names if n in text_lower)
                b_match = next(n for n in b_names if n in text_lower)

                found_interactions.append({
                    "drug_a": a_match,
                    "drug_b": b_match,
                    "severity": effective_severity,
                    "description": interaction["description"],
                    "source": interaction["source"],
                    "has_warning": has_warning,
                })

        if not found_interactions:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="No known drug interactions detected.",
            )

        max_severity = Severity.INFO
        for item in found_interactions:
            sev = Severity(item["severity"])
            if sev > max_severity:
                max_severity = sev

        pairs = [f"{i['drug_a']}+{i['drug_b']}" for i in found_interactions[:3]]
        suffix = f" (+{len(found_interactions) - 3} more)" if len(found_interactions) > 3 else ""

        warn_note = ""
        all_warned = all(i["has_warning"] for i in found_interactions)
        if all_warned:
            warn_note = " (text includes warnings)"

        status = CheckStatus.FAIL if max_severity >= Severity.WARNING and not all_warned else CheckStatus.WARNING

        return CheckResult(
            check_name=self.name,
            status=status,
            severity=max_severity,
            message=f"Known interaction detected: {', '.join(pairs)}{suffix}{warn_note}",
            details={
                "interactions": found_interactions,
                "recommendation": "Ensure adequate warnings are included when discussing drug interactions.",
            },
        )
