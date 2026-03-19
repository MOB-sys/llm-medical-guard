"""Command-line interface for llm-medical-guard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from llm_medical_guard.guard import MedicalGuard
from llm_medical_guard.result import Severity


# ANSI colors
_COLORS = {
    Severity.DANGER: "\033[91m",  # red
    Severity.WARNING: "\033[93m",  # yellow
    Severity.CAUTION: "\033[94m",  # blue
    Severity.INFO: "\033[92m",  # green
}
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"


def _colorize(text: str, severity: Severity) -> str:
    return f"{_COLORS.get(severity, '')}{text}{_RESET}"


def _print_result(result, verbose: bool = False) -> None:
    # Header
    if result.passed:
        icon = _colorize("PASS", Severity.INFO)
        print(f"\n  {_BOLD}{icon}{_RESET}  Score: {result.score:.0%}  |  All {len(result.checks)} checks passed.\n")
    else:
        icon = _colorize("FAIL", result.severity)
        print(f"\n  {_BOLD}{icon}{_RESET}  Score: {result.score:.0%}  |  Severity: {_colorize(result.severity.value.upper(), result.severity)}\n")

    # Check details
    for check in result.checks:
        if check.passed:
            status = _colorize("PASS", Severity.INFO)
        else:
            status = _colorize("FAIL", check.severity)

        print(f"  {status}  {check.check_name}: {check.message}")

        # Show suggestions in verbose mode
        if verbose and not check.passed and "suggestions" in check.details:
            for expr, suggestion in check.details["suggestions"].items():
                print(f"    {_DIM}'{expr}' → '{suggestion}'{_RESET}")

    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-medical-guard",
        description="Safety guardrails for LLM-generated medical content.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # check command
    check_parser = subparsers.add_parser("check", help="Check text for medical safety")
    check_parser.add_argument("text", nargs="?", help="Text to check (or pipe via stdin)")
    check_parser.add_argument("-f", "--file", help="Read text from file")
    check_parser.add_argument("-l", "--locale", default="en", help="Language (en, ko, ja, zh, es)")
    check_parser.add_argument("-c", "--config", help="YAML config file path")
    check_parser.add_argument("--checks", nargs="+", help="Enable only specific checks")
    check_parser.add_argument("--strict", action="store_true", help="Exit with code 1 on failure")
    check_parser.add_argument("-v", "--verbose", action="store_true", help="Show suggestions")
    check_parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")

    # bench command
    bench_parser = subparsers.add_parser("bench", help="Run performance benchmark")
    bench_parser.add_argument("-n", "--iterations", type=int, default=10000, help="Number of iterations")
    bench_parser.add_argument("-l", "--locale", default="en", help="Language")

    # badge command
    badge_parser = subparsers.add_parser("badge", help="Generate verification badge")
    badge_parser.add_argument("text", nargs="?", help="Text to check")
    badge_parser.add_argument("-f", "--file", help="Read text from file")
    badge_parser.add_argument("-o", "--output", default="medical-guard-badge.svg", help="Output SVG path")
    badge_parser.add_argument("-l", "--locale", default="en", help="Language")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "check":
        return _cmd_check(args)
    elif args.command == "bench":
        return _cmd_bench(args)
    elif args.command == "badge":
        return _cmd_badge(args)

    return 0


def _get_text(args) -> str:
    if args.text:
        return args.text
    if hasattr(args, "file") and args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Error: No text provided. Use positional argument, --file, or pipe via stdin.", file=sys.stderr)
    sys.exit(1)


def _cmd_check(args) -> int:
    text = _get_text(args)

    guard = MedicalGuard(
        config=args.config,
        locale=args.locale,
        checks=args.checks,
    )

    result = guard.check(text)

    if args.json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        _print_result(result, verbose=args.verbose)

    if args.strict and not result.passed:
        return 1
    return 0


def _cmd_bench(args) -> int:
    import time

    guard = MedicalGuard(locale=args.locale)
    n = args.iterations

    samples = [
        "Take 5000 IU of vitamin D daily to cure your cold.",
        "Omega-3 fatty acids may support heart health. Consult your doctor. Source: NIH.",
        "This miracle cure has no side effects! Better than your doctor!",
        "Acetaminophen 500mg every 6 hours as needed. Not a substitute for professional medical advice.",
        "비타민D는 뼈 건강에 도움이 될 수 있습니다. 의사와 상담하세요. 식약처 DUR 기반.",
    ]

    print(f"\n  Benchmarking llm-medical-guard ({args.locale})")
    print(f"  {n:,} iterations × {len(samples)} samples = {n * len(samples):,} total checks\n")

    start = time.perf_counter()
    for _ in range(n):
        for sample in samples:
            guard.check(sample)
    elapsed = time.perf_counter() - start

    total = n * len(samples)
    per_check = elapsed / total * 1_000_000  # microseconds

    print(f"  Total time:    {elapsed:.2f}s")
    print(f"  Per check:     {per_check:.1f}µs")
    print(f"  Throughput:    {total / elapsed:,.0f} checks/sec\n")

    return 0


def _cmd_badge(args) -> int:
    from llm_medical_guard.badge import generate_badge

    text = _get_text(args)
    guard = MedicalGuard(locale=args.locale)
    result = guard.check(text)
    generate_badge(result, args.output)
    print(f"Badge saved to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
