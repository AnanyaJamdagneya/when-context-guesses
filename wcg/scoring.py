"""Score reconstructions: target-word exact match and a small exact test for paired outcomes."""

from math import comb


def normalize_word(token: str) -> str:
    """Lowercase and strip surrounding punctuation ("Bed." -> "bed"). Inner characters are kept."""
    start, end = 0, len(token)
    while start < end and not token[start].isalnum():
        start += 1
    while end > start and not token[end - 1].isalnum():
        end -= 1
    return token[start:end].lower()


def extract_target(reconstruction: str, target_position: int) -> str | None:
    """Return the normalized word at the target position, or None if the sentence is too short.

    This assumes the model kept the word order. If it added or dropped words, the
    visible-character check flags the item and the reviewer should look at it by hand.
    """
    tokens = reconstruction.split()
    if target_position >= len(tokens):
        return None
    return normalize_word(tokens[target_position])


def is_exact_match(predicted: str | None, target_word: str) -> bool:
    """Exact spelling match only: synonyms or near-misses count as incorrect."""
    return predicted is not None and predicted == target_word.lower()


def exact_sign_test(b: int, c: int) -> float:
    """Two-sided exact binomial (McNemar-style) p-value for discordant pair counts b and c.

    b = pairs where only the predictable version was recovered,
    c = pairs where only the unexpected version was recovered.
    With 12 pairs this test has very little power; treat it as descriptive.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)
