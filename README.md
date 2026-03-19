<p align="center">
  <img src="https://img.shields.io/pypi/v/llm-medical-guard?color=blue" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/llm-medical-guard" alt="Python">
  <img src="https://img.shields.io/github/license/pillright/llm-medical-guard" alt="License">
  <img src="https://img.shields.io/github/stars/pillright/llm-medical-guard?style=social" alt="Stars">
</p>

# llm-medical-guard

> Safety guardrails for LLM-generated medical and health content.

**The first open-source library specifically designed to validate medical content from LLMs.**

Generic guardrail tools (NeMo Guardrails, Guardrails AI, LLM Guard) handle toxicity and PII but know nothing about medicine. `llm-medical-guard` catches dangerous medical claims, validates dosages, enforces disclaimers, and suggests safe alternatives — in 6 languages.

## Why?

LLMs confidently generate medical misinformation. A model might say *"Take 50,000 IU of Vitamin D daily to cure depression"* — that's a dangerous dosage with an unsubstantiated cure claim. This library catches both issues in microseconds, with zero API calls.

## Quick Start

```bash
pip install llm-medical-guard
```

```python
from llm_medical_guard import MedicalGuard

guard = MedicalGuard()

# Check LLM output
result = guard.check(
    "Take 50000 IU of vitamin D daily to cure your depression. "
    "This miracle supplement has no side effects!"
)

print(result.passed)    # False
print(result.severity)  # Severity.DANGER
print(result.summary)
# 4/6 checks failed:
#   - [DANGER] banned_expressions: Prohibited expression detected: 'cure', 'miracle ...', 'no side effects'
#   - [WARNING] claim_severity: Medical claim detected: 'cure your depression'
#   - [WARNING] disclaimer: Required medical disclaimer not found
#   - [DANGER] dosage: Dosage issue: vitamin d: 50000.0IU far exceeds max recommended 4000IU/day
```

### Safe alternatives included

```python
for check in result.failed_checks:
    if "suggestions" in check.details:
        for expr, suggestion in check.details["suggestions"].items():
            print(f"  '{expr}' → '{suggestion}'")

# 'cure' → 'may help manage symptoms'
# 'miracle ...' → 'evidence-based treatment option'
# 'no side effects' → 'side effects are uncommon but possible'
```

## Features

| Check | What it catches | Severity |
|-------|----------------|----------|
| **Banned Expressions** | Cure claims, fear-mongering, anti-professional statements | DANGER |
| **Claim Severity** | Unsubstantiated treatment/prevention claims | WARNING |
| **Disclaimer** | Missing medical disclaimers | WARNING |
| **Source Attribution** | No authoritative source cited (FDA, NIH, etc.) | WARNING |
| **Dosage** | Vitamin/supplement doses exceeding safe limits | DANGER |
| **Brand Mention** | Pharmaceutical brand names (promotional risk) | CAUTION |

### Key Differentiators

- **Medical-specific** — Not generic content moderation. Understands dosages, drug claims, and medical regulations.
- **Safe alternatives** — Doesn't just block; suggests compliant replacements.
- **Multi-language** — English, Korean, Japanese out of the box. Easily extensible.
- **Zero LLM cost** — Pure regex/rule-based. Runs in microseconds. No API keys needed.
- **Battle-tested rules** — Ported from a production health content pipeline.
- **Framework integrations** — LangChain and OpenAI SDK support.

## Multi-Language Support

```python
# Korean
guard_ko = MedicalGuard(locale="ko")
result = guard_ko.check("이 약을 먹으면 암 예방이 됩니다!")
# Catches: "암 예방" (cancer prevention claim)

# Japanese
guard_ja = MedicalGuard(locale="ja")
result = guard_ja.check("この薬は万能薬です。完治します。")
# Catches: "万能薬" (cure-all), "完治" (complete cure)
```

## Configuration

### YAML Config

```yaml
# guard_config.yaml
locale: en
strict: false
checks:
  banned_expressions: true
  claim_severity: true
  disclaimer: true
  source_attribution: false  # disable for chatbot use
  dosage: true
  brand_mention: false
custom_banned_expressions:
  - "detox cleanse"
  - "alkaline water cure"
custom_safe_alternatives:
  "detox cleanse": "support your body's natural detoxification"
```

```python
guard = MedicalGuard(config="guard_config.yaml")
```

### Programmatic Config

```python
guard = MedicalGuard(
    config={
        "custom_banned_expressions": ["snake oil", "miracle juice"],
        "custom_brands": ["HealthMax", "VitaBoost"],
    },
    locale="en",
    strict=True,  # raises MedicalGuardError on failure
)
```

### Selective Checks

```python
# Only run specific checks
guard = MedicalGuard(checks=["banned_expressions", "dosage"])
```

## Framework Integrations

### LangChain

```python
from langchain_openai import ChatOpenAI
from llm_medical_guard.integrations.langchain import MedicalGuardParser

llm = ChatOpenAI(model="gpt-4o")
parser = MedicalGuardParser(locale="en")
chain = llm | parser

# Raises OutputParserException if content is unsafe
result = chain.invoke("What supplements help with sleep?")
```

### OpenAI SDK

```python
from llm_medical_guard.integrations.openai_wrapper import guarded_chat_completion

response, guard_result = guarded_chat_completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Tell me about vitamin D dosage"}],
)

if not guard_result.passed:
    print("Content flagged:", guard_result.summary)
```

## Dosage Database

Built-in safe dosage limits for common supplements:

| Supplement | Max Daily | Warning Threshold | Unit |
|-----------|----------|-------------------|------|
| Vitamin D | 4,000 | 10,000 | IU |
| Vitamin C | 2,000 | 5,000 | mg |
| Iron | 45 | 100 | mg |
| Calcium | 2,500 | 4,000 | mg |
| Zinc | 40 | 100 | mg |
| Omega-3 | 3,000 | 5,000 | mg |
| Magnesium | 400 | 800 | mg |
| Melatonin | 5 | 20 | mg |
| Vitamin A | 3,000 | 10,000 | mcg |
| Vitamin B6 | 100 | 200 | mg |

## Extending

### Custom Check

```python
from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.result import CheckResult, CheckStatus, Severity

@CheckRegistry.register
class MyCustomCheck(BaseCheck):
    name = "my_check"
    description = "My custom medical content check"

    def run(self, text, config):
        if "unapproved" in text.lower():
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.FAIL,
                severity=Severity.WARNING,
                message="Unapproved content detected",
            )
        return CheckResult(
            check_name=self.name,
            status=CheckStatus.PASS,
            severity=Severity.INFO,
            message="OK",
        )
```

### Custom Locale

Create a YAML file following the format in `src/llm_medical_guard/i18n/en.yaml` and load it:

```python
guard = MedicalGuard(locale="de")  # will look for i18n/de.yaml
```

## Why Not Use General Guardrails?

| Feature | llm-medical-guard | NeMo Guardrails | Guardrails AI | LLM Guard |
|---------|:-----------------:|:---------------:|:-------------:|:---------:|
| Medical claim detection | Yes | No | No | No |
| Dosage validation | Yes | No | No | No |
| Safe alternatives | Yes | No | No | No |
| Medical disclaimer enforcement | Yes | No | No | No |
| Source attribution check | Yes | No | No | No |
| Multi-language medical rules | Yes | No | Partial | No |
| Zero API cost | Yes | No | Partial | Yes |
| Medical-specific taxonomy | Yes | No | No | No |

## Roadmap

- [ ] Chinese (zh) and Spanish (es) locale support
- [ ] Drug-drug interaction warnings
- [ ] ICD-10 code detection
- [ ] FHIR resource validation
- [ ] Streaming support (check chunks as they arrive)
- [ ] pytest plugin for CI/CD health content testing

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Priority areas:
- New locale files (especially zh, es, de, fr, pt)
- Additional dosage limits for supplements/drugs
- Better regex patterns for medical claims
- Integration with more LLM frameworks

## License

[MIT](LICENSE) — Use freely in commercial and open-source projects.

## Disclaimer

This library is a development tool for content safety screening. It does not provide medical advice and is not a substitute for professional medical review. Always have medical content reviewed by qualified healthcare professionals before publication.

---

Built with domain expertise from [Pillright](https://pillright.com) — a drug interaction checker serving 500K+ users.
