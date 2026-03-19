"""Streaming support for real-time LLM output checking."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from llm_medical_guard.guard import MedicalGuard
from llm_medical_guard.result import GuardResult


class StreamGuard:
    """Accumulates streaming LLM chunks and runs guard checks periodically.

    Usage:
        from llm_medical_guard.stream import StreamGuard

        stream_guard = StreamGuard(locale="en")

        for chunk in llm_stream:
            alert = stream_guard.feed(chunk.content)
            if alert:
                print(f"Warning: {alert.summary}")
                # Optionally stop the stream

        # Final check on complete text
        final_result = stream_guard.finalize()
    """

    def __init__(
        self,
        guard: MedicalGuard | None = None,
        locale: str = "en",
        check_interval: int = 200,
    ):
        self._guard = guard or MedicalGuard(locale=locale)
        self._buffer = ""
        self._check_interval = check_interval
        self._chars_since_check = 0
        self._last_result: GuardResult | None = None

    @property
    def text(self) -> str:
        return self._buffer

    @property
    def last_result(self) -> GuardResult | None:
        return self._last_result

    def feed(self, chunk: str) -> GuardResult | None:
        """Feed a chunk of streaming text. Returns GuardResult if a check was triggered."""
        self._buffer += chunk
        self._chars_since_check += len(chunk)

        if self._chars_since_check >= self._check_interval:
            self._chars_since_check = 0
            result = self._guard.check(self._buffer)
            self._last_result = result
            if not result.passed:
                return result

        return None

    def finalize(self) -> GuardResult:
        """Run final check on the complete accumulated text."""
        self._last_result = self._guard.check(self._buffer)
        return self._last_result

    def reset(self) -> None:
        """Reset the buffer for a new stream."""
        self._buffer = ""
        self._chars_since_check = 0
        self._last_result = None


def check_stream(
    chunks: Iterable[str],
    guard: MedicalGuard | None = None,
    locale: str = "en",
    check_interval: int = 200,
) -> Iterator[tuple[str, GuardResult | None]]:
    """Generator that yields (chunk, alert_or_none) tuples.

    Usage:
        for chunk, alert in check_stream(llm_chunks):
            print(chunk, end="")
            if alert:
                print(f"\\nWarning: {alert.summary}")
    """
    sg = StreamGuard(guard=guard, locale=locale, check_interval=check_interval)
    for chunk in chunks:
        alert = sg.feed(chunk)
        yield chunk, alert
