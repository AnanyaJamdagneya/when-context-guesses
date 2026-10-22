from wcg import config
from wcg.dataset import build_items, load_dataset
from wcg.masking import mask_positions, mask_sentence


def test_half_the_letters_are_masked_rounded_down():
    assert len(mask_positions(5, "P01", 1)) == 2
    assert len(mask_positions(8, "P01", 1)) == 4


def test_positions_are_reproducible_and_depend_on_pair():
    assert mask_positions(8, "P05", 42) == mask_positions(8, "P05", 42)
    # Different pairs should not all share one pattern (would make the seed meaningless).
    patterns = {mask_positions(8, f"P{i:02d}", 42) for i in range(1, 13)}
    assert len(patterns) > 1


def test_mask_sentence_keeps_punctuation_and_rest_of_sentence():
    masked = mask_sentence("I went to bed.", 3, "bed", (0,))
    assert masked == "I went to _ed."


def test_both_versions_of_every_pair_share_mask_positions():
    items = build_items(load_dataset(config.DATASET_PATH), config.SEED)
    masked = [i for i in items if i.input_type == "masked"]
    by_pair = {}
    for item in masked:
        by_pair.setdefault(item.pair_id, set()).add(item.mask_positions)
        # Only the target word changes: the masked input differs from the original
        # in exactly len(word)//2 characters, all of them underscores.
        diffs = [(a, b) for a, b in zip(item.original, item.model_input) if a != b]
        assert len(diffs) == len(item.target_word) // 2
        assert all(b == "_" for _, b in diffs)
    assert all(len(positions) == 1 for positions in by_pair.values())


def test_intact_items_are_unchanged():
    items = build_items(load_dataset(config.DATASET_PATH), config.SEED)
    assert all(i.model_input == i.original for i in items if i.input_type == "intact")


def test_repeats_share_input_but_get_separate_cache_keys():
    from wcg.runner import cache_key

    items = build_items(load_dataset(config.DATASET_PATH), config.SEED, ("P01",), repeats=3)
    masked = [i for i in items if i.base_id == "P01-predictable-masked"]
    assert len(masked) == 3
    assert len({i.model_input for i in masked}) == 1
    settings = config.load_settings(mock=True)
    assert len({cache_key(i, settings) for i in masked}) == 3


def test_pattern_matching_counts_words_that_fit():
    from wcg.patterns import matching_words, pattern_info

    words = ("house", "horse", "hoist", "mouse", "horses")
    assert matching_words("ho_s_", words) == ["house", "horse", "hoist"]
    info = pattern_info("ho_s_", "horse", words)
    assert info["candidate_count"] == 3 and info["target_frequency_rank"] == 2
