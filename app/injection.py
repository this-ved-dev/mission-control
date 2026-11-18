"""Code-level backstop for prompt injection, OR-ed with the model's check."""

import re

INJECTION = re.compile(
    r"ignore (all |any )?(previous|prior|above|earlier) instructions|you are now|"
    r"set (the )?verdict|\bsystem\s*:|disregard (the )?(rules|limits|instructions)|"
    r"override mode|do not mention this",
    re.IGNORECASE,
)


def injection_phrase(note: str) -> str | None:
    match = INJECTION.search(note)
    return match.group(0) if match else None
