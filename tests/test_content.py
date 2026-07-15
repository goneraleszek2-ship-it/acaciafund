"""Tests for core/content.py — Content dataclass wrapper."""

from datetime import datetime, timezone

import pytest

from core.content import Content


class TestContentCreation:
    def test_minimal_dict(self):
        c = Content.from_dict({"slug": "test/slug", "title": "Test Title", "pillar": "aml"})
        assert c.slug == "test/slug"
        assert c.title == "Test Title"
        assert c.pillar == "aml"
        assert c.content_type == "research"

    def test_full_dict(self):
        data = {
            "slug": "markets/research/test",
            "title": "Market Research Test",
            "pillar": "stock",
            "content_type": "research",
            "tags": ["markets", "research"],
            "description": "A test description",
            "body_html": "<p>Test body</p>",
            "difficulty": "intermediate",
            "author": "Test Author",
            "sqi": 0.85,
            "enriched": True,
        }
        c = Content.from_dict(data)
        assert c.tags == ["markets", "research"]
        assert c.description == "A test description"
        assert c.body_html == "<p>Test body</p>"
        assert c.difficulty == "intermediate"
        assert c.author == "Test Author"
        assert c.sqi == 0.85
        assert c.enriched is True

    def test_created_at_parsing(self):
        c = Content.from_dict({"slug": "t", "title": "T", "pillar": "aml", "created_at": "2026-06-15T10:00:00Z"})
        assert c.created_at is not None
        assert c.created_at.year == 2026
        assert c.created_at.month == 6
        assert c.created_at.day == 15

    def test_created_at_invalid(self):
        c = Content.from_dict({"slug": "t", "title": "T", "pillar": "aml", "created_at": "not-a-date"})
        assert c.created_at is None

    def test_tags_falls_back_to_category(self):
        c = Content.from_dict({"slug": "t", "title": "T", "pillar": "aml", "category": "test-cat"})
        assert c.tags == ["test-cat"]

    def test_default_values(self):
        c = Content.from_dict({"slug": "t", "title": "T", "pillar": "stock"})
        assert c.content_type == "research"
        assert c.tags == []
        assert c.body_html == ""
        assert c.sqi == 0.0
        assert c.author == "AcaciaFund"
        assert c.enriched is False
        assert c.knowledge_category == "reference"


class TestContentFields:
    def test_bloom_questions_default(self):
        c = Content(slug="s", title="T", pillar="aml", content_type="research")
        assert c.bloom_questions == []

    def test_quality_flags_default(self):
        c = Content(slug="s", title="T", pillar="aml", content_type="research")
        assert c.quality_flags == []

    def test_signals_default(self):
        c = Content(slug="s", title="T", pillar="aml", content_type="research")
        assert c.signals is None

    def test_source_breakdown_default(self):
        c = Content(slug="s", title="T", pillar="aml", content_type="research")
        assert c.source_breakdown is None

    def test_flashcards_default(self):
        c = Content(slug="s", title="T", pillar="aml", content_type="research")
        assert c.flashcards == []
