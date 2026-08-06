"""Tests for core/journeys.py (Tier 3.3 cross-pillar journeys)."""

import json

from core.journeys import JOURNEYS, build_journey_pages, build_journeys_index

REGISTRY = json.load(open("registry.json"))["content"]


def test_three_curated_journeys():
    assert len(JOURNEYS) == 3


def test_every_item_slug_exists_in_registry():
    slugs = {i["slug"] for i in REGISTRY}
    for journey in JOURNEYS:
        for slug in journey["items"]:
            assert slug in slugs, f"{journey['slug']} references missing {slug}"


def test_each_journey_spans_all_three_pillars():
    for journey in JOURNEYS:
        pillars = {slug.split("/", 1)[0] for slug in journey["items"]}
        assert pillars == {"markets", "aml", "data"}, journey["slug"]


def test_pages_resolve_steps_with_links():
    pages = build_journey_pages(REGISTRY)
    assert len(pages) == 3
    for page in pages:
        assert page["step_count"] == len(page["steps"]) >= 6
        for step in page["steps"]:
            assert step["url"].startswith("/") and step["url"].endswith("/")
            assert step["title"]
            assert step["pillar"] in ("aml", "stock", "data-engineering")


def test_prev_next_linkage_is_linear():
    for page in build_journey_pages(REGISTRY):
        steps = page["steps"]
        for i, step in enumerate(steps):
            if i == 0:
                assert step["prev"] is None
            else:
                assert step["prev"]["slug"] == steps[i - 1]["slug"]
            if i == len(steps) - 1:
                assert step["next"] is None
            else:
                assert step["next"]["slug"] == steps[i + 1]["slug"]


def test_pillar_span_counts():
    for page in build_journey_pages(REGISTRY):
        assert page["span_count"] == 3


def test_index_entries_have_first_url():
    pages = build_journey_pages(REGISTRY)
    for entry in build_journeys_index(pages):
        assert entry["first_url"].startswith("/")
        assert entry["slug"] in {p["slug"] for p in pages}
