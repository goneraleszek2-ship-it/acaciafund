"""Tests for core/extractors.py — deterministic text extractors."""

from core.extractors import (
    extract_comparisons,
    extract_flow,
    extract_timeline,
)

# ── extract_timeline ──


class TestExtractTimeline:
    def test_empty_text_returns_empty(self):
        assert extract_timeline("") == []
        assert extract_timeline("<p></p>") == []

    def test_extracts_year_mentions(self):
        text = "The event occurred in 2024. It was a significant milestone."
        result = extract_timeline(text)
        assert len(result) >= 1
        assert "2024" in result[0]["date"]

    def test_extracts_month_year(self):
        text = "In March 2024, the company launched its platform."
        result = extract_timeline(text)
        assert any("2024" in r["date"] for r in result)

    def test_skips_years_out_of_range(self):
        text = "Founded in 1950, the company grew until 2025."
        result = extract_timeline(text)
        for r in result:
            assert "1950" not in r["date"]

    def test_quarter_format(self):
        text = "By Q1 '25, revenue doubled."
        result = extract_timeline(text)
        assert len(result) >= 1
        assert "Q1" in result[0]["date"]

    def test_returns_at_most_12_events(self):
        text = ("In 2020. " * 50)
        result = extract_timeline(text)
        assert len(result) <= 12

    def test_events_are_chronological(self):
        text = "In 2024 we launched. In 2022 we started. In 2025 we expanded."
        result = extract_timeline(text)
        dates = [r["date"] for r in result]
        assert dates == sorted(dates)

    def test_skips_short_events(self):
        text = "In 2024 a short event. In 2025 a much longer description of something important."
        result = extract_timeline(text)
        for r in result:
            assert len(r["event"]) > 20


# ── extract_flow ──


class TestExtractFlow:
    def test_empty_text_returns_empty(self):
        assert extract_flow("") == []

    def test_no_flow_keywords_returns_empty(self):
        text = "This article discusses general topics without any specific sequence."
        assert extract_flow(text) == []

    def test_numbered_steps_detected(self):
        text = "The pipeline process follows these steps. Step 1: Ingest raw data from multiple sources. Step 2: Transform and validate all fields. Step 3: Load into target warehouse."
        result = extract_flow(text)
        assert len(result) >= 1
        assert any("ingest" in r["description"].lower() for r in result)

    def test_arrow_format_detected(self):
        text = "The deployment pipeline goes: build source code → run automated tests → deploy to production environment."
        result = extract_flow(text)
        assert len(result) >= 1

    def test_narrative_steps_detected(self):
        text = (
            "The compliance workflow proceeds as follows. First, we collect all customer identification documents. "
            "Then, we verify identities against government databases. Finally, we flag any discrepancies for review."
        )
        result = extract_flow(text)
        assert len(result) >= 1
        assert any("identification" in r["description"] for r in result)


# ── extract_comparisons ──


class TestExtractComparisons:
    def test_empty_text_returns_empty(self):
        assert extract_comparisons("") == []

    def test_x_vs_y_detected(self):
        text = (
            "In performance testing, Tool A handles 1200 records per second vs Tool B "
            "and the difference grows under load."
        )
        result = extract_comparisons(text)
        assert len(result) >= 1
        assert any("Tool A" in r["entity_a"] for r in result)

    def test_growth_percentage_detected(self):
        text = (
            "In the benchmark evaluation, revenue grew 25% while operating "
            "costs declined 10% year over year."
        )
        result = extract_comparisons(text)
        assert len(result) >= 1

    def test_percentage_range_detected(self):
        text = (
            "The classification accuracy increased from 80% to 95% for the new "
            "machine learning model after retraining."
        )
        result = extract_comparisons(text)
        assert len(result) >= 1

    def test_returns_at_most_5_comparisons(self):
        text = ("Tool A vs Tool B. " * 20)
        result = extract_comparisons(text)
        assert len(result) <= 5
