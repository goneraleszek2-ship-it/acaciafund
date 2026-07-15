"""Tests for core/compositor.py — SVG compositing engine."""

import re

from core.compositor import (
    PILLAR_COMPOSITOR_COLORS,
    render_comparisons,
    render_connections,
    render_entity_badges,
    render_flow,
    render_key_numbers,
    render_timeline,
)


def _is_svg(result: str) -> bool:
    return result.startswith("<svg") and result.endswith("</svg>")


def _svg_contains(result: str, text: str) -> bool:
    return text in result


# ── render_timeline ──


class TestRenderTimeline:
    def test_empty_returns_empty_string(self):
        assert render_timeline([]) == ""

    def test_single_event_returns_svg(self):
        result = render_timeline([{"date": "2026-01", "event": "Launch"}])
        assert _is_svg(result)
        assert _svg_contains(result, "2026-01")
        assert _svg_contains(result, "Launch")

    def test_multiple_events(self):
        events = [
            {"date": "Jan", "event": "Start"},
            {"date": "Feb", "event": "Middle"},
            {"date": "Mar", "event": "End"},
        ]
        result = render_timeline(events)
        assert _is_svg(result)
        assert _svg_contains(result, "Jan")
        assert _svg_contains(result, "Mar")
        assert _svg_contains(result, "TIMELINE")

    def test_custom_dimensions(self):
        result = render_timeline([{"date": "D", "event": "E"}], width=800, height=200)
        assert _is_svg(result)
        assert 'width="800"' in result
        assert 'height="200"' in result

    def test_pillar_color_applied(self):
        result = render_timeline(
            [{"date": "D", "event": "E"}], pillar="stock"
        )
        stock_line = PILLAR_COMPOSITOR_COLORS["stock"]["line"]
        assert stock_line in result


# ── render_flow ──


class TestRenderFlow:
    def test_empty_returns_empty_string(self):
        assert render_flow([]) == ""

    def test_single_step_returns_svg(self):
        result = render_flow([{"step": "1", "description": "Collect data"}])
        assert _is_svg(result)
        assert _svg_contains(result, "Collect data")
        assert _svg_contains(result, "FLOW")

    def test_multiple_steps_with_arrows(self):
        steps = [
            {"step": "1", "description": "Ingest"},
            {"step": "2", "description": "Transform"},
        ]
        result = render_flow(steps)
        assert _is_svg(result)
        assert _svg_contains(result, "Ingest")
        assert _svg_contains(result, "Transform")

    def test_custom_dimensions(self):
        result = render_flow(
            [{"step": "1", "description": "A"}], width=500, height=150
        )
        assert 'width="500"' in result
        assert 'height="150"' in result


# ── render_comparisons ──


class TestRenderComparisons:
    def test_empty_returns_empty_string(self):
        assert render_comparisons([]) == ""

    def test_single_comparison_returns_svg(self):
        comp = [
            {
                "entity_a": "Tool A",
                "entity_b": "Tool B",
                "metric": "speed",
                "value_a": "100",
                "value_b": "80",
            }
        ]
        result = render_comparisons(comp)
        assert _is_svg(result)
        assert _svg_contains(result, "Tool A")
        assert _svg_contains(result, "COMPARISONS")

    def test_handles_missing_fields_gracefully(self):
        comp = [{"entity_a": "X", "value_a": "1"}]
        result = render_comparisons(comp)
        assert _is_svg(result)

    def test_custom_dimensions(self):
        comp = [{"entity_a": "A", "entity_b": "B", "value_a": "1", "value_b": "2"}]
        result = render_comparisons(comp, width=700, height=120)
        assert 'width="700"' in result
        assert 'height="120"' in result


# ── render_entity_badges ──


class TestRenderEntityBadges:
    def test_empty_returns_empty_string(self):
        assert render_entity_badges([]) == ""

    def test_single_entity_returns_svg(self):
        result = render_entity_badges(["FATF"])
        assert _is_svg(result)
        assert _svg_contains(result, "FATF")
        assert _svg_contains(result, "KEY ENTITIES")

    def test_multiple_entities(self):
        result = render_entity_badges(["AML", "KYC", "SAR", "CDD"])
        assert _is_svg(result)
        for e in ("AML", "KYC", "SAR", "CDD"):
            assert e in result

    def test_entity_truncated_at_25_chars(self):
        result = render_entity_badges(["A" * 50])
        assert "A" * 25 in result
        assert "A" * 26 not in result


# ── render_key_numbers ──


class TestRenderKeyNumbers:
    def test_empty_returns_empty_string(self):
        assert render_key_numbers([]) == ""

    def test_single_number_returns_svg(self):
        result = render_key_numbers([{"value": "99%", "label": "Accuracy"}])
        assert _is_svg(result)
        assert _svg_contains(result, "99%")
        assert _svg_contains(result, "Accuracy")
        assert _svg_contains(result, "KEY NUMBERS")

    def test_multiple_numbers(self):
        items = [
            {"value": "100", "label": "Cases"},
            {"value": "50%", "label": "Rate"},
        ]
        result = render_key_numbers(items)
        assert _is_svg(result)
        assert _svg_contains(result, "100")
        assert _svg_contains(result, "50%")

    def test_all_items_rendered(self):
        items = [{"value": str(i), "label": f"L{i}"} for i in range(10)]
        result = render_key_numbers(items)
        assert _is_svg(result)
        assert _svg_contains(result, "L5")
        assert _svg_contains(result, "L9")


# ── render_connections ──


class TestRenderConnections:
    def test_empty_returns_empty_string(self):
        assert render_connections([]) == ""

    def test_single_connection_returns_svg(self):
        result = render_connections(["Cross-pillar: AML + Data"])
        assert _is_svg(result)
        assert _svg_contains(result, "CONNECTIONS")

    def test_multiple_connections(self):
        result = render_connections(["AML↔Data", "Markets↔AML"])
        assert _is_svg(result)


# ── Pillar colors ──


class TestPillarColors:
    def test_unknown_pillar_falls_back_to_gray(self):
        result = render_timeline(
            [{"date": "D", "event": "E"}], pillar="nonexistent"
        )
        assert _is_svg(result)

    def test_all_pillars_have_colors(self):
        for pillar in ("aml", "stock", "data-engineering"):
            assert pillar in PILLAR_COMPOSITOR_COLORS
            pal = PILLAR_COMPOSITOR_COLORS[pillar]
            for key in ("line", "fill", "text", "border"):
                assert key in pal
                assert pal[key]
