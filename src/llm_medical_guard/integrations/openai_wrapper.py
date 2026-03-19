"""OpenAI SDK integration for llm-medical-guard."""

from __future__ import annotations

from typing import Any

try:
    import openai
except ImportError as e:
    raise ImportError(
        "OpenAI integration requires the openai package. "
        "Install with: pip install llm-medical-guard[openai]"
    ) from e

from llm_medical_guard.guard import MedicalGuard
from llm_medical_guard.result import GuardResult


def guarded_chat_completion(
    guard: MedicalGuard | None = None,
    **kwargs: Any,
) -> tuple[Any, GuardResult]:
    """Wrapper around openai.chat.completions.create with medical guardrails.

    Usage:
        from llm_medical_guard.integrations.openai_wrapper import guarded_chat_completion

        response, guard_result = guarded_chat_completion(
            model="gpt-4o",
            messages=[{"role": "user", "content": "What supplements help with sleep?"}],
        )

        if not guard_result.passed:
            print("Content flagged:", guard_result.summary)

    Returns:
        Tuple of (ChatCompletion response, GuardResult).
    """
    if guard is None:
        guard = MedicalGuard()

    client = openai.OpenAI()
    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content or ""

    result = guard.check(text)

    if guard.config.strict and not result.passed:
        result.raise_on_fail()

    return response, result
