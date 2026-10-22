"""The single prompt and response schema used for every item."""

# Bump this if the wording changes; it is part of the cache key, so old responses
# are never mixed with responses to a different prompt.
PROMPT_VERSION = "v2"

PROMPT_TEMPLATE = """You will see one English sentence. Some letters may have been replaced with underscores (_). Each underscore stands for exactly one missing letter.

Reconstruct the complete sentence.
- Copy every visible character exactly as shown, including capitalization, spaces, and punctuation.
- Replace each underscore with exactly one letter.
- If the sentence contains no underscores, return it exactly as shown.

Also report:
- "confident": true if you are confident your reconstruction matches the original sentence, otherwise false.
- "other_possible_words": any other words that could have been the original where letters are missing. Use an empty list if there are none.

<sentence>{sentence}</sentence>"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "reconstruction": {"type": "string"},
        "confident": {"type": "boolean"},
        "other_possible_words": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["reconstruction", "confident", "other_possible_words"],
    "additionalProperties": False,
}


def build_prompt(model_input: str) -> str:
    return PROMPT_TEMPLATE.format(sentence=model_input)
