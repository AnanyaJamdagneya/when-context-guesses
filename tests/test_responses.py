from wcg.dataset import Item
from wcg.report import evaluate_item
from wcg.responses import parse_response_text, visible_character_violations

ITEM = Item(
    item_id="P01-unexpected-masked", pair_id="P01", condition="unexpected", input_type="masked",
    original="I brushed my horse before going to bed.", model_input="I brushed my ho_s_ before going to bed.",
    target_word="horse", target_position=3, mask_positions=(2, 4),
)


def ok_record(raw_text, stop_reason="end_turn"):
    return {"status": "ok", "raw_text": raw_text, "stop_reason": stop_reason}


def test_parse_valid_json():
    assert parse_response_text('{"reconstruction": "Hi there."}').reconstruction == "Hi there."


def test_parse_failures_are_reported_not_guessed():
    assert parse_response_text("").error
    assert parse_response_text("I think it says horse").error
    assert parse_response_text('{"answer": "x"}').error


def test_visible_character_check():
    shown = "I brushed my ho_s_ before going to bed."
    assert visible_character_violations(shown, "I brushed my horse before going to bed.") == []
    assert visible_character_violations(shown, "I brushed my house before going to bed.") == []  # legal fill
    assert visible_character_violations(shown, "I brushed my hoses before going to bed.")  # visible "s" changed to "e"
    assert visible_character_violations(shown, "I brushed my horses before going to bed.")  # length changed


def test_blank_filled_with_non_letter_is_a_violation():
    assert visible_character_violations("a_c", "a-c")


def test_wrong_but_faithful_answer_is_incorrect_without_violation():
    row = evaluate_item(ITEM, ok_record('{"reconstruction": "I brushed my house before going to bed."}'))
    assert row["target_correct"] is False
    assert row["visible_char_violation"] is False
    assert row["failure"] == ""


def test_correct_answer():
    row = evaluate_item(ITEM, ok_record('{"reconstruction": "I brushed my horse before going to bed."}'))
    assert row["target_correct"] is True


def test_failures_are_separated_from_wrong_answers():
    assert evaluate_item(ITEM, None)["failure"] == "not_run"
    assert evaluate_item(ITEM, {"status": "api_error", "error": "500"})["failure"] == "api_error"
    assert evaluate_item(ITEM, ok_record("not json"))["failure"] == "parse_error"
    assert evaluate_item(ITEM, ok_record("", stop_reason="refusal"))["failure"] == "refusal"
    assert evaluate_item(ITEM, ok_record("", stop_reason="max_tokens"))["failure"] == "truncated"
