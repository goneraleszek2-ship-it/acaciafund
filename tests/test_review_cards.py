"""Contract tests for core/review_cards.py (flashcard collection + index)."""

import json

from core.review_cards import collect_flashcards, write_flashcard_index


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
