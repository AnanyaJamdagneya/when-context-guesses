"""The single prompt and response schema used for every item."""

# Bump this if the wording changes; it is part of the cache key, so old responses
# are never mixed with responses to a different prompt.
PROMPT_VERSION = "v1"

PROMPT_TEMPLATE = """You will see one English sentence. Some letters may have been replaced with underscores (_). Each underscore stands for exactly one missing letter.

Reconstruct the complete sentence.
- Copy every visible character exactly as shown, including capitalization, spaces, and punctuation.
- Replace each underscore with exactly one letter.
- If the sentence contains no underscores, return it exactly as shown.

<sentence>{sentence}</sentence>"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"reconstruction": {"type": "string"}},
    "required": ["reconstruction"],
    "additionalProperties": False,
}


def build_prompt(model_input: str) -> str:
    return PROMPT_TEMPLATE.format(sentence=model_input)
