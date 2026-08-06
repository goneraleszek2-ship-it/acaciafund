"""Contract tests for core/review_cards.py (flashcard collection + index)."""

import json

from core.review_cards import (
    backfill_flashcards_from_quizzes,
    collect_flashcards,
    write_flashcard_index,
)


class _Item:
    def __init__(self, data):
        self.__dict__["_data"] = data

    def model_dump(self):
        return self._data


def test_collects_cards_with_term_definition():
    items = [
        {"slug": "data/learn/x", "pillar": "data-engineering", "flashcards": [
            {"term": "OLAP", "definition": "Online analytical processing"},
        ]},
    ]
    cards = collect_flashcards(items)
    assert len(cards) == 1
    assert cards[0]["id"] == "data/learn/x#0"
    assert cards[0]["term"] == "OLAP"
    assert cards[0]["definition"] == "Online analytical processing"
    assert cards[0]["pillar"] == "data-engineering"


def test_supports_front_back_fallback():
    items = [
        {"slug": "a", "pillar": "aml", "flashcards": [
            {"front": "Q1", "back": "A1"},
        ]},
    ]
    cards = collect_flashcards(items)
    assert cards[0]["term"] == "Q1"
    assert cards[0]["definition"] == "A1"


def test_skips_items_without_flashcards():
    items = [
        {"slug": "a", "pillar": "aml", "flashcards": []},
        {"slug": "b", "pillar": "stock"},
    ]
    assert collect_flashcards(items) == []


def test_skips_blank_terms():
    items = [{"slug": "a", "pillar": "aml", "flashcards": [{"term": "", "definition": "x"}]}]
    assert collect_flashcards(items) == []


def test_handles_pydantic_like_objects():
    item = _Item({"slug": "a", "pillar": "aml", "flashcards": [{"term": "T", "definition": "D"}]})
    cards = collect_flashcards([item])
    assert cards[0]["id"] == "a#0"


def test_index_multiple_cards_numbered():
    items = [{"slug": "a", "pillar": "aml", "flashcards": [
        {"term": "T1", "definition": "D1"},
        {"term": "T2", "definition": "D2"},
    ]}]
    cards = collect_flashcards(items)
    assert [c["id"] for c in cards] == ["a#0", "a#1"]


def test_write_flashcard_index(tmp_path):
    cards = [{"id": "a#0", "term": "T", "definition": "D", "pillar": "aml", "slug": "a"}]
    out = tmp_path / "static" / "flashcard_index.json"
    write_flashcard_index(cards, out)
    payload = json.loads(out.read_text())
    assert payload["total"] == 1
    assert payload["cards"][0]["id"] == "a#0"
    assert payload["cards"][0]["term"] == "T"
    assert "definition" not in payload["cards"][0]


def _learn_item(slug="a/learn/x", flashcards=None, questions=None):
    return {
        "slug": slug,
        "pillar": "aml",
        "content_type": "learn",
        "flashcards": flashcards or [],
        "bloom_questions": questions or [],
    }


def test_no_backfill_when_already_min_cards():
    item = _learn_item(flashcards=[{"term": "T1", "definition": "D1"}, {"term": "T2", "definition": "D2"}, {"term": "T3", "definition": "D3"}])
    assert backfill_flashcards_from_quizzes(item) == item["flashcards"]


def test_backfill_pads_to_three_from_quiz_correct():
    item = _learn_item(
        flashcards=[{"term": "T1", "definition": "D1"}],
        questions=[{"question": "Q1?", "correct": "A1", "level": "remember"}],
    )
    cards = backfill_flashcards_from_quizzes(item)
    assert len(cards) == 2
    assert cards[1] == {"term": "Q1?", "definition": "A1"}


def test_backfill_answer_text_from_options_index():
    item = _learn_item(
        flashcards=[{"term": "T1", "definition": "D1"}],
        questions=[{
            "type": "mc", "question": "Q1?",
            "options": ["Wrong", "Right"], "answer": 1, "level": "analyze",
        }],
    )
    cards = backfill_flashcards_from_quizzes(item)
    assert cards[1]["definition"] == "Right"


def test_backfill_stops_at_min_cards():
    item = _learn_item(
        flashcards=[{"term": "T1", "definition": "D1"}, {"term": "T2", "definition": "D2"}],
        questions=[
            {"question": "Q1?", "correct": "A1"},
            {"question": "Q2?", "correct": "A2"},
            {"question": "Q3?", "correct": "A3"},
        ],
    )
    cards = backfill_flashcards_from_quizzes(item)
    assert len(cards) == 3
    assert cards[2] == {"term": "Q1?", "definition": "A1"}


def test_backfill_skips_questions_without_answer():
    item = _learn_item(
        flashcards=[{"term": "T1", "definition": "D1"}],
        questions=[{"question": "Q1?", "level": "remember"}, {"question": "Q2?", "correct": "A2"}],
    )
    cards = backfill_flashcards_from_quizzes(item)
    assert len(cards) == 2
    assert cards[1]["term"] == "Q2?"


def test_backfill_only_applies_to_learn_items():
    item = _learn_item(flashcards=[{"term": "T1", "definition": "D1"}])
    item["content_type"] = "research"
    assert backfill_flashcards_from_quizzes(item) == item["flashcards"]


def test_collect_flashcards_includes_backfilled_cards():
    items = [_learn_item(
        flashcards=[{"term": "T1", "definition": "D1"}],
        questions=[{"question": "Q1?", "correct": "A1"}, {"question": "Q2?", "correct": "A2"}],
    )]
    cards = collect_flashcards(items)
    assert [c["id"] for c in cards] == ["a/learn/x#0", "a/learn/x#1", "a/learn/x#2"]
    assert cards[1]["term"] == "Q1?"
    assert cards[2]["term"] == "Q2?"
