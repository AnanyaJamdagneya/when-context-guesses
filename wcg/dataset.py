"""Load, validate, and expand the sentence-pair dataset into experiment items."""

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

from .masking import mask_positions, mask_sentence
from .scoring import normalize_word

REQUIRED_COLUMNS = ["pair_id", "condition", "sentence", "target_word", "target_position"]
CONDITIONS = ("predictable", "unexpected")
INPUT_TYPES = ("intact", "masked")


class DatasetError(ValueError):
    pass


@dataclass(frozen=True)
class Sentence:
    pair_id: str
    condition: str
    sentence: str
    target_word: str
    target_position: int  # 0-based index of the word when the sentence is split on spaces


@dataclass(frozen=True)
class Item:
    """One request to the model: a sentence in either its intact or masked form."""

    item_id: str
    pair_id: str
    condition: str
    input_type: str
    original: str
    model_input: str
    target_word: str
    target_position: int
    mask_positions: tuple[int, ...]
    repeat: int  # 1..REPEATS; each repeat is an independent request with the same prompt

    @property
    def base_id(self) -> str:
        """The item without its repeat number, e.g. 'P01-unexpected-masked'."""
        return f"{self.pair_id}-{self.condition}-{self.input_type}"


def dataset_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_dataset(path: Path) -> list[Sentence]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise DatasetError(f"Dataset is missing columns: {missing}")
        sentences = []
        for line_no, row in enumerate(reader, start=2):
            try:
                position = int(row["target_position"])
            except ValueError:
                raise DatasetError(f"Line {line_no}: target_position must be an integer")
            sentences.append(
                Sentence(
                    pair_id=row["pair_id"].strip(),
                    condition=row["condition"].strip(),
                    sentence=row["sentence"].strip(),
                    target_word=row["target_word"].strip(),
                    target_position=position,
                )
            )
    validate(sentences)
    return sentences


def validate(sentences: list[Sentence]) -> None:
    """Check the rules the experiment depends on. Reports every problem at once."""
    problems = []
    pairs: dict[str, dict[str, Sentence]] = {}

    for s in sentences:
        label = f"{s.pair_id}/{s.condition}"
        if s.condition not in CONDITIONS:
            problems.append(f"{label}: condition must be one of {CONDITIONS}")
        if not s.target_word.isalpha():
            problems.append(f"{label}: target word must contain only letters")
        if "  " in s.sentence:
            problems.append(f"{label}: sentence contains a double space")
        tokens = s.sentence.split(" ")
        if not 0 <= s.target_position < len(tokens):
            problems.append(f"{label}: target_position {s.target_position} is outside the sentence")
        elif normalize_word(tokens[s.target_position]) != s.target_word.lower():
            problems.append(
                f"{label}: word at position {s.target_position} is {tokens[s.target_position]!r}, "
                f"not {s.target_word!r}"
            )
        if s.condition in pairs.setdefault(s.pair_id, {}):
            problems.append(f"{label}: duplicate condition in pair")
        pairs[s.pair_id][s.condition] = s

    for pair_id, members in pairs.items():
        if set(members) != set(CONDITIONS):
            problems.append(f"{pair_id}: needs exactly one predictable and one unexpected sentence")
            continue
        p, u = members["predictable"], members["unexpected"]
        if len(p.target_word) != len(u.target_word):
            problems.append(f"{pair_id}: target words differ in length ({p.target_word} vs {u.target_word})")
        if p.target_position != u.target_position:
            problems.append(f"{pair_id}: target positions differ")
        elif _frame(p) != _frame(u):
            problems.append(f"{pair_id}: sentences differ somewhere other than the target word")

    if problems:
        raise DatasetError("Dataset problems:\n  - " + "\n  - ".join(problems))


def _frame(s: Sentence) -> list[str]:
    """The sentence with the target word replaced by a placeholder, for comparing pair structure."""
    tokens = s.sentence.split(" ")
    if 0 <= s.target_position < len(tokens):
        token = tokens[s.target_position]
        start = token.lower().find(s.target_word.lower())
        if start >= 0:
            tokens[s.target_position] = token[:start] + "<TARGET>" + token[start + len(s.target_word) :]
    return tokens


def build_items(
    sentences: list[Sentence], seed: int, pair_ids: tuple[str, ...] | None = None, repeats: int = 1
) -> list[Item]:
    items = []
    for s in sentences:
        if pair_ids is not None and s.pair_id not in pair_ids:
            continue
        positions = mask_positions(len(s.target_word), s.pair_id, seed)
        for input_type in INPUT_TYPES:
            model_input = (
                s.sentence
                if input_type == "intact"
                else mask_sentence(s.sentence, s.target_position, s.target_word, positions)
            )
            for repeat in range(1, repeats + 1):
                items.append(
                    Item(
                        item_id=f"{s.pair_id}-{s.condition}-{input_type}-r{repeat}",
                        pair_id=s.pair_id,
                        condition=s.condition,
                        input_type=input_type,
                        original=s.sentence,
                        model_input=model_input,
                        target_word=s.target_word,
                        target_position=s.target_position,
                        mask_positions=positions if input_type == "masked" else (),
                        repeat=repeat,
                    )
                )
    return items
