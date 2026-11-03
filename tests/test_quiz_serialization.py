"""Quiz payloads must be JSON-safe before landing in an HTML attribute."""

import json
from types import SimpleNamespace

from core.build_content import _serialize_quiz


def test_serialize_quiz_returns_mapping_with_apostrophes():
    item = SimpleNamespace(
        bloom_questions=[
            {
                "question": "Which statement about Snowflake's architecture is correct?",
                "type": "mc",
                "options": ["A", "B"],
                "answer": 0,
            }
        ]
    )
    payload = _serialize_quiz(item)
    assert isinstance(payload, dict)
    assert payload["questions"][0]["q"].startswith("Which statement about Snowflake's")
    # The template's |tojson filter can encode this without breaking the attribute.
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "Snowflake's" in encoded
    assert json.loads(encoded)["questions"]


def test_serialize_quiz_empty_returns_empty_mapping():
    assert _serialize_quiz(SimpleNamespace(bloom_questions=[])) == {}
