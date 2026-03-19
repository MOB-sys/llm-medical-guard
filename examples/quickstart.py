"""Quick start example for llm-medical-guard."""

from llm_medical_guard import MedicalGuard

guard = MedicalGuard()

# Example 1: Dangerous content
print("=" * 60)
print("Example 1: Dangerous LLM output")
print("=" * 60)

result = guard.check(
    "Take 50000 IU of vitamin D daily to cure your depression. "
    "This miracle supplement has no side effects! "
    "Doctors don't want you to know this secret."
)

print(f"Passed: {result.passed}")
print(f"Severity: {result.severity.value}")
print(f"Score: {result.score:.0%}")
print(f"\n{result.summary}")

# Show safe alternatives
print("\nSuggested alternatives:")
for check in result.failed_checks:
    if "suggestions" in check.details:
        for expr, suggestion in check.details["suggestions"].items():
            print(f"  '{expr}' → '{suggestion}'")

# Example 2: Safe content
print("\n" + "=" * 60)
print("Example 2: Safe LLM output")
print("=" * 60)

result = guard.check(
    "Vitamin D may help support bone health when taken at recommended doses "
    "(typically 600-1000 IU daily for most adults). "
    "According to NIH guidelines, the upper limit is 4000 IU per day. "
    "This is not a substitute for professional medical advice. "
    "Consult your healthcare provider before starting any supplement."
)

print(f"Passed: {result.passed}")
print(f"Score: {result.score:.0%}")
print(f"\n{result.summary}")
