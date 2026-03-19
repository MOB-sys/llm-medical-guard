"""Generate 'Medical Content Verified' SVG badges."""

from __future__ import annotations

from llm_medical_guard.result import GuardResult, Severity

_BADGE_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}">
  <title>{label}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{left_width}" height="20" fill="#555"/>
    <rect x="{left_width}" width="{right_width}" height="20" fill="{color}"/>
    <rect width="{width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text aria-hidden="true" x="{left_center}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)">{left_text}</text>
    <text x="{left_center}" y="140" transform="scale(.1)">{left_text}</text>
    <text aria-hidden="true" x="{right_center}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)">{right_text}</text>
    <text x="{right_center}" y="140" transform="scale(.1)">{right_text}</text>
  </g>
</svg>"""

_SEVERITY_COLORS = {
    Severity.DANGER: "#e05d44",
    Severity.WARNING: "#dfb317",
    Severity.CAUTION: "#007ec6",
    Severity.INFO: "#4c1",
}


def generate_badge(result: GuardResult, output_path: str = "medical-guard-badge.svg") -> str:
    """Generate an SVG badge based on guard result."""
    if result.passed:
        right_text = f"passed {result.score:.0%}"
        color = _SEVERITY_COLORS[Severity.INFO]
    else:
        right_text = f"{result.severity.value} {result.score:.0%}"
        color = _SEVERITY_COLORS[result.severity]

    left_text = "medical guard"
    left_width = len(left_text) * 7 + 10
    right_width = len(right_text) * 7 + 10
    width = left_width + right_width

    svg = _BADGE_TEMPLATE.format(
        width=width,
        left_width=left_width,
        right_width=right_width,
        left_center=left_width * 5,
        right_center=(left_width + right_width / 2) * 10,
        left_text=left_text,
        right_text=right_text,
        color=color,
        label=f"medical guard: {right_text}",
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)

    return svg
