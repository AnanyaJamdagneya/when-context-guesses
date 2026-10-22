"""How many common English words fit a blank pattern like 'ho_s_'?

This measures how much the visible letters alone narrow down the answer, independent
of sentence context. It uses the `wordfreq` English list, which is a frequency list
(it includes some names and abbreviations), so counts are approximate.
"""

import re
from functools import lru_cache

from .masking import MASK_CHAR


@lru_cache(maxsize=1)
def english_words(size: int) -> tuple[str, ...]:
    from wordfreq import top_n_list

    return tuple(w for w in top_n_list("en", size) if w.isascii() and w.isalpha())


def matching_words(pattern: str, words: tuple[str, ...]) -> list[str]:
    """Words of the same length that agree with every visible letter, most frequent first."""
    regex = re.compile("^" + re.escape(pattern.lower()).replace(MASK_CHAR, "[a-z]") + "$")
    return [w for w in words if regex.match(w)]


def word_frequency(word: str) -> float:
    """Zipf frequency: about 3 = rare-ish, 5 = very common. Measures familiarity, not fit in context."""
    from wordfreq import zipf_frequency

    return zipf_frequency(word, "en")


def pattern_info(pattern: str, target_word: str, words: tuple[str, ...]) -> dict:
    candidates = matching_words(pattern, words)
    target = target_word.lower()
    return {
        "pattern": pattern,
        "target_zipf_frequency": word_frequency(target),
        "candidate_count": len(candidates),
        "target_frequency_rank": candidates.index(target) + 1 if target in candidates else None,
        "most_frequent_candidates": candidates[:3],
    }
