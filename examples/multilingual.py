"""Multi-language example for llm-medical-guard."""

from llm_medical_guard import MedicalGuard

# English
print("=== English ===")
guard_en = MedicalGuard(locale="en")
result = guard_en.check("This miracle cure has no side effects!")
print(f"Passed: {result.passed} | {result.summary}\n")

# Korean
print("=== 한국어 ===")
guard_ko = MedicalGuard(locale="ko")
result = guard_ko.check("이 약을 먹으면 암 예방이 됩니다! 만병통치약!")
print(f"통과: {result.passed} | {result.summary}\n")

# Japanese
print("=== 日本語 ===")
guard_ja = MedicalGuard(locale="ja")
result = guard_ja.check("この薬は万能薬です。副作用なし！")
print(f"合格: {result.passed} | {result.summary}")
