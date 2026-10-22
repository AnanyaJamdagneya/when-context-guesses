import pytest

from wcg.scoring import exact_sign_test, extract_target, is_exact_match, normalize_word


def test_normalize_ignores_case_and_surrounding_punctuation():
    assert normalize_word("Bed.") == "bed"
    assert normalize_word('"umbrella,"') == "umbrella"
    assert normalize_word("mother's") == "mother's"


def test_synonyms_and_near_misses_are_not_exact_matches():
    assert is_exact_match("teeth", "teeth")
    assert is_exact_match("teeth", "Teeth")
    assert not is_exact_match("tooth", "teeth")
    assert not is_exact_match("pony", "horse")
    assert not is_exact_match(None, "horse")


def test_extract_target_uses_word_position():
    assert extract_target("I brushed my Horse before going to bed.", 3) == "horse"
    assert extract_target("Too short.", 5) is None


def test_sign_test_values():
    assert exact_sign_test(0, 0) == 1.0
    assert exact_sign_test(3, 3) == 1.0
    # 6 vs 0 discordant pairs: 2 * (1/64)
    assert exact_sign_test(6, 0) == pytest.approx(2 / 64)
    assert exact_sign_test(0, 6) == exact_sign_test(6, 0)
