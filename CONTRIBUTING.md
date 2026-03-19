# Contributing to llm-medical-guard

Thank you for your interest in contributing!

## How to Contribute

### Adding a New Locale

1. Copy `src/llm_medical_guard/i18n/en.yaml` to `src/llm_medical_guard/i18n/{lang_code}.yaml`
2. Translate all expressions, patterns, and messages
3. Add tests in `tests/test_guard.py`
4. Submit a PR

### Adding New Checks

1. Create a new file in `src/llm_medical_guard/checks/`
2. Extend `BaseCheck` and register with `@CheckRegistry.register`
3. Import in `guard.py` to trigger registration
4. Add tests

### Improving Rules

- Add banned expressions with safe alternatives
- Expand dosage limits for more supplements
- Improve regex patterns to reduce false positives

## Development Setup

```bash
git clone https://github.com/pillright/llm-medical-guard.git
cd llm-medical-guard
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Code Style

- Use `ruff` for linting
- Use `mypy` for type checking
- Write tests for all new features
- Keep functions under 50 lines

## PR Guidelines

- One feature per PR
- Include tests
- Update README if adding user-facing features
