"""Tests for the Graphics-as-Code pipeline: extractors and compositor."""

from core.extractors import (
    extract_timeline, extract_flow, extract_comparisons,
    extract_entities_from_analysis, extract_numbers_from_analysis,
    extract_sqi_from_analysis, extract_timeline_from_trending,
)
from core.compositor import (
    render_timeline, render_flow, render_comparisons,
    render_entity_badges, render_key_numbers, render_connections,
    auto_compose,
)


# ── Timeline extraction ────────────────────────────────────────

def test_timeline_extracts_month_year():
    html = "<p>The EU published new rules in March 2024.</p>"
    result = extract_timeline(html)
    assert len(result) >= 1
    assert "March 2024" in result[0]["date"]
    assert len(result[0]["event"]) > 10


def test_timeline_extracts_year_with_preposition():
    html = "<p>By 2025, all member states must comply.</p>"
    result = extract_timeline(html)
    assert len(result) >= 1
    assert result[0]["date"] == "2025"


def test_timeline_extracts_month_day_year():
    html = "<p>On January 15, 2024 the regulation took effect.</p>"
    result = extract_timeline(html)
    assert len(result) >= 1
    assert "Jan" in result[0]["date"]
    assert "2024" in result[0]["date"]


def test_timeline_cross_sentence_boundary():
    html = "<p>First event happened in March 2024. Second event followed in April 2024.</p>"
    result = extract_timeline(html)
    assert len(result) >= 1


def test_timeline_ignores_out_of_range_year():
    html = "<p>The year 1969 was before the internet. By 2050 AI will dominate.</p>"
    result = extract_timeline(html)
    # 1969 < 1970, 2050 > 2030 — both out of range
    assert len(result) == 0


def test_timeline_sorts_chronologically():
    html = "<p>In 2025 the rules tightened. By March 2024 it was proposed. In January 2023 it was drafted.</p>"
    result = extract_timeline(html)
    dates = [r["date"] for r in result]
    # Should be: Jan 2023, Mar 2024, 2025
    assert "January 2023" in dates or "Jan 2023" in str(result[0])
    # Check that 2025 comes after 2024
    y_2025 = next(i for i, d in enumerate(dates) if "2025" in d)
    m_2024 = next(i for i, d in enumerate(dates) if "March 2024" in d or "Mar 2024" in d)
    assert m_2024 < y_2025


def test_timeline_empty_text():
    assert extract_timeline("") == []
    assert extract_timeline("<p>No dates here.</p>") == []


def test_timeline_max_12_events():
    html = "<p>In 2020 event.</p><p>In 2021 event.</p><p>In 2022 event.</p><p>In 2023 event.</p><p>In 2024 event.</p><p>In 2025 event.</p><p>In 2026 event.</p><p>In 2027 event.</p><p>In 2028 event.</p><p>In 2029 event.</p><p>In 2030 event.</p><p>In 2031 event.</p><p>In 2032 event.</p>"
    result = extract_timeline(html)
    assert len(result) <= 12


# ── Flow extraction ────────────────────────────────────────────

def test_flow_numbered_steps():
    html = "<p>Step 1: Verify customer identity. Step 2: Screen sanctions. Step 3: File report.</p>"
    result = extract_flow(html)
    assert len(result) >= 2
    assert any("Verify" in r["description"] for r in result)


def test_flow_arrow_pattern():
    html = "<p>The transaction is flagged by the system \u2192 reviewed by compliance \u2192 reported to FIU.</p>"
    result = extract_flow(html)
    assert len(result) >= 1
    assert "system" in result[0]["description"] or "reviewed" in result[0]["description"]


def test_flow_requires_keyword():
    # Text that looks like steps but without flow keyword should be skipped
    html = "<p>Apple makes phones. Google makes search. Microsoft makes Windows.</p>"
    result = extract_flow(html)
    assert len(result) == 0


def test_flow_first_then_finally():
    html = "<p>First, the transaction is flagged, then it is reviewed by compliance, finally it is reported.</p>"
    result = extract_flow(html)
    assert len(result) >= 2


def test_flow_empty_text():
    assert extract_flow("") == []
    assert extract_flow("<p>Hello world.</p>") == []


# ── Comparison extraction ──────────────────────────────────────

def test_comparison_vs_pattern():
    html = "<p>Airflow vs Prefect — two orchestration tools.</p>"
    result = extract_comparisons(html)
    assert len(result) >= 1
    assert "Airflow" in result[0]["entity_a"] or "Airflow" in result[0]["entity_b"]


def test_comparison_percentage_change():
    html = "<p>Revenue grew by 45% in 2024.</p>"
    result = extract_comparisons(html)
    assert len(result) >= 1
    assert "45%" in result[0]["value_a"]


def test_comparison_milestone():
    html = "<p>The company reached 85% market share in the region.</p>"
    result = extract_comparisons(html)
    assert len(result) >= 1


def test_comparison_empty_text():
    assert extract_comparisons("") == []
    assert extract_comparisons("<p>Just a plain sentence.</p>") == []


# ── Analysis HTML extractors ───────────────────────────────────

ANALYSIS_SAMPLE = (
    "**Key entities:** `TSMC` · `2nm` · `NVIDIA` · `ASML`\n"
    "**Key numbers:** 892 · 18 · 7\n"
    "**SQI:** 0.85"
)


def test_extract_entities():
    result = extract_entities_from_analysis(ANALYSIS_SAMPLE)
    assert "TSMC" in result
    assert "NVIDIA" in result
    assert len(result) <= 8


def test_extract_entities_removes_noise():
    # Stop words like "a", "the" should be filtered
    html = "**Key entities:** `the` · `a` · `TSMC` · `of`"
    result = extract_entities_from_analysis(html)
    assert "TSMC" in result
    assert "the" not in result
    assert "a" not in result


def test_extract_entities_empty():
    assert extract_entities_from_analysis("") == []
    assert extract_entities_from_analysis("**Key entities:** ``") == []


def test_extract_numbers():
    result = extract_numbers_from_analysis(ANALYSIS_SAMPLE)
    assert len(result) >= 3
    assert any("892" in r["value"] for r in result)


def test_extract_numbers_empty():
    assert extract_numbers_from_analysis("") == []


def test_extract_sqi():
    assert extract_sqi_from_analysis(ANALYSIS_SAMPLE) == 0.85


def test_extract_sqi_none():
    assert extract_sqi_from_analysis("") is None
    assert extract_sqi_from_analysis("**Key entities:** TSMC") is None


TRENDING_SAMPLE = """
## Top Story (HackerNews, 2026-06-07)
1. [Meta is notifying thousands of users about account hijacks](https://news.ycombinator.com/item?id=123)
2. [New data breach affects millions](https://news.ycombinator.com/item?id=456)
"""


def test_extract_timeline_from_trending():
    result = extract_timeline_from_trending(TRENDING_SAMPLE)
    assert len(result) >= 2
    assert all(r["date"] == "2026-06-07" for r in result)
    assert "Meta" in result[0]["event"] or "account hijacks" in result[0]["event"]


def test_extract_timeline_from_trending_empty():
    assert extract_timeline_from_trending("") == []
    assert extract_timeline_from_trending("<p>No trending data</p>") == []


# ── Compositor: Timeline SVG ───────────────────────────────────

def test_render_timeline():
    events = [
        {"date": "Jan 2023", "event": "Regulation proposed"},
        {"date": "Mar 2024", "event": "Regulation enacted"},
    ]
    svg = render_timeline(events, pillar="aml")
    assert svg.startswith("<svg")
    assert "gac-timeline" in svg
    assert "Jan 2023" in svg
    assert "Mar 2024" in svg
    assert "Regulation proposed" in svg
    assert "#d97706" in svg  # AML amber
    assert svg.endswith("</svg>")


def test_render_timeline_empty():
    assert render_timeline([]) == ""
    assert render_timeline([], pillar="stock") == ""


def test_render_timeline_data_engineering_color():
    events = [{"date": "2024", "event": "Kafka 4.0 released"}]
    svg = render_timeline(events, pillar="data-engineering")
    assert "#6366f1" in svg  # indigo


# ── Compositor: Flow SVG ───────────────────────────────────────

def test_render_flow():
    steps = [
        {"step": 1, "description": "Verify identity"},
        {"step": 2, "description": "Screen sanctions"},
    ]
    svg = render_flow(steps, pillar="aml")
    assert svg.startswith("<svg")
    assert "gac-flow" in svg
    assert "Verify identity" in svg
    assert svg.endswith("</svg>")


def test_render_flow_empty():
    assert render_flow([]) == ""


def test_render_flow_marker_def():
    steps = [{"step": 1, "description": "Step one"}, {"step": 2, "description": "Step two"}]
    svg = render_flow(steps)
    assert "marker" in svg


# ── Compositor: Comparison SVG ─────────────────────────────────

def test_render_comparison():
    comps = [{"entity_a": "Airflow", "entity_b": "Prefect", "metric": "comparison", "value_a": "", "value_b": ""}]
    svg = render_comparisons(comps, pillar="data-engineering")
    assert svg.startswith("<svg")
    assert "gac-comparison" in svg
    assert "Airflow" in svg
    assert svg.endswith("</svg>")


def test_render_comparison_empty():
    assert render_comparisons([]) == ""


# ── Compositor: Entity Badges SVG ──────────────────────────────

def test_render_entity_badges():
    entities = ["TSMC", "NVIDIA", "ASML", "Apple"]
    svg = render_entity_badges(entities, pillar="stock")
    assert svg.startswith("<svg")
    assert "gac-entities" in svg
    assert "TSMC" in svg
    assert "NVIDIA" in svg
    assert svg.endswith("</svg>")


def test_render_entity_badges_empty():
    assert render_entity_badges([]) == ""
    assert render_entity_badges([], pillar="aml") == ""


# ── Compositor: Key Numbers SVG ────────────────────────────────

def test_render_key_numbers():
    numbers = [{"value": "892", "label": "HN points"}, {"value": "18", "label": "sources"}, {"value": "7", "label": "domains"}]
    svg = render_key_numbers(numbers, pillar="aml")
    assert svg.startswith("<svg")
    assert "gac-numbers" in svg
    assert "892" in svg
    assert "HN points" in svg
    assert svg.endswith("</svg>")


def test_render_key_numbers_empty():
    assert render_key_numbers([]) == ""
    assert render_key_numbers([], pillar="stock") == ""


# ── Compositor: Connections SVG ────────────────────────────────

def test_render_connections():
    conns = ["Connects to AML", "Connects to Science"]
    svg = render_connections(conns, pillar="aml")
    assert svg.startswith("<svg")
    assert "gac-connections" in svg
    assert "Connects to AML" in svg
    assert svg.endswith("</svg>")


def test_render_connections_empty():
    assert render_connections([]) == ""


# ── Auto-compose integration ───────────────────────────────────

def test_auto_compose_timeline_and_flow():
    text = "<p>In January 2023 the rules were proposed. By March 2024 they were enacted.</p><p>Step 1: Register the entity. Step 2: Verify the identity. Step 3: Report the findings.</p>"
    results = auto_compose(text, pillar="aml")
    types = {r["type"] for r in results}
    assert "timeline" in types
    assert "flow" in types
    for r in results:
        assert "svg" in r
        assert r["svg"].startswith("<svg")


def test_auto_compose_empty_text():
    assert auto_compose("") == []
    assert auto_compose("<p>Hello world.</p>") == []


def test_auto_compose_respects_width():
    text = "<p>In January 2023 A happened. By March 2024 B happened. In 2025 C happened.</p>"
    results = auto_compose(text, pillar="stock", width=400)
    assert len(results) >= 1
    assert 'width="400"' in results[0]["svg"]
