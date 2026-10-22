from wcg.dataset import Item
from wcg.report import evaluate_item
from wcg.responses import parse_response_text, visible_character_violations

ITEM = Item(
    item_id="P01-unexpected-masked", pair_id="P01", condition="unexpected", input_type="masked",
    original="I brushed my horse before going to bed.", model_input="I brushed my ho_s_ before going to bed.",
    target_word="horse", target_position=3, mask_positions=(2, 4), repeat=1,
)


def answer(reconstruction, confident=True, others=()):
    import json

    return json.dumps({"reconstruction": reconstruction, "confident": confident, "other_possible_words": list(others)})


def ok_record(raw_text, stop_reason="end_turn"):
    return {"status": "ok", "raw_text": raw_text, "stop_reason": stop_reason}


def test_parse_valid_json():
    parsed = parse_response_text(answer("Hi there.", confident=False, others=["Hello"]))
    assert parsed.reconstruction == "Hi there."
    assert parsed.confident is False
    assert parsed.other_possible_words == ("Hello",)


def test_parse_failures_are_reported_not_guessed():
    assert parse_response_text("").error
    assert parse_response_text("I think it says horse").error
    assert parse_response_text('{"answer": "x"}').error
    assert parse_response_text('{"reconstruction": "x"}').error  # confidence fields missing
    assert parse_response_text('{"reconstruction": "x", "confident": "yes", "other_possible_words": []}').error


def test_visible_character_check():
    shown = "I brushed my ho_s_ before going to bed."
    assert visible_character_violations(shown, "I brushed my horse before going to bed.") == []
    assert visible_character_violations(shown, "I brushed my house before going to bed.") == []  # legal fill
    assert visible_character_violations(shown, "I brushed my hoses before going to bed.")  # visible "s" changed to "e"
    assert visible_character_violations(shown, "I brushed my horses before going to bed.")  # length changed


def test_blank_filled_with_non_letter_is_a_violation():
    assert visible_character_violations("a_c", "a-c")


def test_wrong_but_faithful_answer_is_incorrect_without_violation():
    row = evaluate_item(ITEM, ok_record(answer("I brushed my house before going to bed.", False, ["Horse"])))
    assert row["target_correct"] is False
    assert row["visible_char_violation"] is False
    assert row["failure"] == ""
    assert row["confident"] is False
    assert row["target_in_other_words"] is True  # alternatives are compared case-insensitively


def test_correct_answer():
    row = evaluate_item(ITEM, ok_record(answer("I brushed my horse before going to bed.")))
    assert row["target_correct"] is True


def test_failures_are_separated_from_wrong_answers():
    assert evaluate_item(ITEM, None)["failure"] == "not_run"
    assert evaluate_item(ITEM, {"status": "api_error", "error": "500"})["failure"] == "api_error"
    assert evaluate_item(ITEM, ok_record("not json"))["failure"] == "parse_error"
    assert evaluate_item(ITEM, ok_record("", stop_reason="refusal"))["failure"] == "refusal"
    assert evaluate_item(ITEM, ok_record("", stop_reason="max_tokens"))["failure"] == "truncated"


def test_majority_rule_across_repeats():
    from dataclasses import replace

    from wcg.report import item_stability

    right = answer("I brushed my horse before going to bed.")
    wrong = answer("I brushed my house before going to bed.")
    rows = [evaluate_item(replace(ITEM, repeat=k), ok_record(t)) for k, t in enumerate([right, wrong, right], 1)]
    assert item_stability(rows)["P01-unexpected-masked"]["recovered"] is True
    rows[2] = evaluate_item(replace(ITEM, repeat=3), {"status": "api_error", "error": "500"})
    # 1 right out of 2 scored is not more than half
    assert item_stability(rows)["P01-unexpected-masked"]["recovered"] is False
