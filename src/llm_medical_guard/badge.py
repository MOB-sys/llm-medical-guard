"""Generate 'Medical Content Verified' SVG badges."""

from __future__ import annotations

from llm_medical_guard.result import GuardResult, Severity

_BADGE_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg"'
    ' width="{width}" height="20"'
    ' role="img" aria-label="{label}">\n'
    "  <title>{label}</title>\n"
    '  <linearGradient id="s" x2="0" y2="100%">\n'
    '    <stop offset="0" stop-color="#bbb"'
    ' stop-opacity=".1"/>\n'
    '    <stop offset="1" stop-opacity=".1"/>\n'
    "  </linearGradient>\n"
    '  <clipPath id="r">\n'
    '    <rect width="{width}" height="20"'
    ' rx="3" fill="#fff"/>\n'
    "  </clipPath>\n"
    '  <g clip-path="url(#r)">\n'
    '    <rect width="{left_width}"'
    ' height="20" fill="#555"/>\n'
    '    <rect x="{left_width}"'
    ' width="{right_width}" height="20"'
    ' fill="{color}"/>\n'
    '    <rect width="{width}" height="20"'
    ' fill="url(#s)"/>\n'
    "  </g>\n"
    '  <g fill="#fff" text-anchor="middle"'
    " font-family="
    '"Verdana,Geneva,DejaVu Sans,sans-serif"'
    ' text-rendering="geometricPrecision"'
    ' font-size="110">\n'
    '    <text aria-hidden="true"'
    ' x="{left_center}" y="150"'
    ' fill="#010101" fill-opacity=".3"'
    ' transform="scale(.1)">'
    "{left_text}</text>\n"
    '    <text x="{left_center}" y="140"'
    ' transform="scale(.1)">'
    "{left_text}</text>\n"
    '    <text aria-hidden="true"'
    ' x="{right_center}" y="150"'
    ' fill="#010101" fill-opacity=".3"'
    ' transform="scale(.1)">'
    "{right_text}</text>\n"
    '    <text x="{right_center}" y="140"'
    ' transform="scale(.1)">'
    "{right_text}</text>\n"
    "  </g>\n"
    "</svg>"
)

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
