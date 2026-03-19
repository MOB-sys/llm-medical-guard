"""LangChain integration for llm-medical-guard."""

from __future__ import annotations

from typing import Any

try:
    from langchain_core.exceptions import OutputParserException
    from langchain_core.output_parsers import BaseOutputParser
except ImportError as e:
    raise ImportError(
        "LangChain integration requires langchain-core. "
        "Install with: pip install llm-medical-guard[langchain]"
    ) from e

from llm_medical_guard.guard import MedicalGuard


class MedicalGuardParser(BaseOutputParser[str]):
    """LangChain output parser that validates medical content safety.

    Usage:
        from llm_medical_guard.integrations.langchain import MedicalGuardParser

        parser = MedicalGuardParser()
        chain = llm | parser
        result = chain.invoke("your prompt")
    """

    guard: Any = None
    locale: str = "en"
    strict: bool = True

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        if self.guard is None:
            self.guard = MedicalGuard(locale=self.locale)

    @property
    def _type(self) -> str:
        return "medical_guard"

    def parse(self, text: str) -> str:
        result = self.guard.check(text)
        if not result.passed:
            raise OutputParserException(
                error=f"Medical content safety check failed:\n{result.summary}",
                observation=text,
            )
        return text
