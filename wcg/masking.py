"""Hide half of a target word's letters at seeded positions."""

import random

MASK_CHAR = "_"


def mask_positions(word_length: int, pair_id: str, seed: int) -> tuple[int, ...]:
    """Choose which letter positions to hide.

    Half the letters (rounded down) are hidden. The random generator is seeded with
    both the project seed and the pair ID, so the two sentences in a pair (whose
    target words have equal length) get identical positions, and reruns are identical.
    """
    count = word_length // 2
    rng = random.Random(f"{seed}:{pair_id}")
    return tuple(sorted(rng.sample(range(word_length), count)))


def mask_word(word: str, positions: tuple[int, ...]) -> str:
    letters = list(word)
    for i in positions:
        letters[i] = MASK_CHAR
    return "".join(letters)


def mask_sentence(sentence: str, target_position: int, target_word: str, positions: tuple[int, ...]) -> str:
    """Replace letters of the target word inside the sentence, leaving everything else intact.

    The token at target_position may carry punctuation (e.g. "bed."), so we locate the
    word inside the token rather than replacing the whole token.
    """
    tokens = sentence.split(" ")
    token = tokens[target_position]
    start = token.lower().find(target_word.lower())
    if start < 0:
        raise ValueError(f"Target {target_word!r} not found in token {token!r}")
    original = token[start : start + len(target_word)]
    tokens[target_position] = token[:start] + mask_word(original, positions) + token[start + len(target_word) :]
    return " ".join(tokens)
