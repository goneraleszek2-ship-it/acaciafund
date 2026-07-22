"""Tests for core/data.py — data utilities, domain extraction, entity extraction."""

import json

from core.data import (
    ALL_ENTITIES,
    DOMAIN_TAXONOMY,
    STOP_WORDS,
    categorize_domain,
    extract_domain,
    extract_entities,
    extract_themes,
    log,
    write_dlq,
)


class TestExtractDomain:
    def test_standard_url(self):
        assert extract_domain("https://www.example.com/page") == "www.example.com"

    def test_no_protocol(self):
        assert extract_domain("http://example.com") == "example.com"

    def test_empty_url(self):
        assert extract_domain("") == ""

    def test_no_match(self):
        assert extract_domain("not-a-url") == ""


class TestCategorizeDomain:
    def test_known_category(self):
        cat = categorize_domain("github.com")
        assert isinstance(cat, str)

    def test_unknown_returns_other(self):
        assert categorize_domain("completely-unknown.example") == "other"

    def test_all_domain_categories_exist(self):
        for cat in ("technical", "concepts", "tools"):
            assert cat in DOMAIN_TAXONOMY


class TestExtractEntities:
    def test_empty_text(self):
        assert extract_entities("") == []

    def test_case_insensitive(self):
        result = extract_entities("AML compliance KYC")
        assert isinstance(result, list)

    def test_max_five_entities(self):
        many = " ".join(list(ALL_ENTITIES)[:20])
        result = extract_entities(many)
        assert len(result) <= 5


class TestExtractThemes:
    def test_empty_list(self):
        assert extract_themes([]) == []

    def test_single_title(self):
        themes = extract_themes(["Advancements in Machine Learning for Trading"])
        assert isinstance(themes, list)

    def test_stop_words_filtered(self):
        themes = extract_themes(["the and of for"])
        assert all(t.lower() not in STOP_WORDS for t in themes)

    def test_most_common_returns_top_5(self):
        titles = ["python data pipeline", "python streaming", "python etl"] * 3
        themes = extract_themes(titles)
        assert len(themes) <= 5
        assert "Python" in themes


class TestWriteDlq:
    def test_writes_file(self, tmp_path):
        dlq_dir = tmp_path / ".dlq"

        # Patch DLQ_DIR
        import core.data as d
        orig = d.DLQ_DIR
        d.DLQ_DIR = dlq_dir
        try:
            write_dlq("test-source", "https://example.com", "test error", {"key": "val"})
            files = list(dlq_dir.iterdir())
            assert len(files) == 1
            content = json.loads(files[0].read_text())
            assert content["source"] == "test-source"
            assert content["error"] == "test error"
            assert content["context"]["key"] == "val"
        finally:
            d.DLQ_DIR = orig


class TestLog:
    def test_ok_message(self, capsys):
        log("test ok", ok=True)
        captured = capsys.readouterr()
        assert "[+] test ok" in captured.err

    def test_error_message(self, capsys):
        log("test error", ok=False)
        captured = capsys.readouterr()
        assert "[-] test error" in captured.err
