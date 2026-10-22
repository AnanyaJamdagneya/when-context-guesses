"""Turn raw model output into a reconstruction and check it against the visible characters."""

import json
from dataclasses import dataclass

from .masking import MASK_CHAR


@dataclass(frozen=True)
class ParsedResponse:
    reconstruction: str | None
    error: str | None
    confident: bool | None = None
    other_possible_words: tuple[str, ...] = ()


def parse_response_text(text: str | None) -> ParsedResponse:
    """Expect {"reconstruction": str, "confident": bool, "other_possible_words": [str]}.

    Anything else is a parsing failure; we never try to guess what a malformed answer meant.
    """
    if not text or not text.strip():
        return ParsedResponse(None, "empty response")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return ParsedResponse(None, f"invalid JSON: {e.msg}")
    if not isinstance(data, dict) or not isinstance(data.get("reconstruction"), str):
        return ParsedResponse(None, "JSON is missing a string 'reconstruction' field")
    if not isinstance(data.get("confident"), bool):
        return ParsedResponse(None, "JSON is missing a true/false 'confident' field")
    others = data.get("other_possible_words")
    if not isinstance(others, list) or not all(isinstance(w, str) for w in others):
        return ParsedResponse(None, "JSON is missing a list of strings in 'other_possible_words'")
    return ParsedResponse(data["reconstruction"].strip(), None, data["confident"], tuple(w.strip() for w in others))


def visible_character_violations(model_input: str, reconstruction: str) -> list[str]:
    """List the ways the reconstruction fails to preserve the input.

    Every visible character must be copied exactly, and every underscore must become
    exactly one letter. An empty list means the reconstruction is faithful to what was shown.
    """
    if len(reconstruction) != len(model_input):
        return [f"length changed from {len(model_input)} to {len(reconstruction)} characters"]
    problems = []
    for i, (shown, written) in enumerate(zip(model_input, reconstruction)):
        if shown == MASK_CHAR:
            if not written.isalpha():
                problems.append(f"position {i}: blank filled with {written!r}, not a letter")
        elif shown != written:
            problems.append(f"position {i}: visible {shown!r} changed to {written!r}")
    return problems
