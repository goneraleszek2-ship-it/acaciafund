"""Contract tests for scripts/backfill_openalex.py.

Network calls are mocked; the script's fetch layer is tested for URL shaping,
error handling, and idempotency guarantees.
"""

import json
from email.message import Message

from scripts.backfill_openalex import (
    OPENALEX_API,
    apply_work_to_item,
    backfill,
    fetch_openalex_work,
)


class FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._payload


def fake_work(cited: int, oa_id: str = "https://openalex.org/W123456") -> dict:
    return {"id": oa_id, "cited_by_count": cited}


def test_api_url_shapes_doi():
    assert OPENALEX_API.format("10.1000/xyz") == "https://api.openalex.org/works/doi:10.1000/xyz"


def test_api_url_quotes_slashes_in_arxiv_doi(monkeypatch):
    # arxiv DOIs contain a slash after the colon; URL must be encoded
    captured = {}

    def fake_urlopen(request, timeout=15.0):
        captured["url"] = request.full_url
        return FakeResponse(json.dumps(fake_work(1)).encode())

    monkeypatch.setattr("scripts.backfill_openalex.urlopen", fake_urlopen)
    fetch_openalex_work("10.48550/arXiv.2607.05307")
    assert captured["url"] == "https://api.openalex.org/works/doi:10.48550%2FarXiv.2607.05307"


def test_fetch_openalex_work_success(monkeypatch):
    def fake_urlopen(request, timeout=15.0):
        assert request.get_header("User-agent").startswith("AcaciaFund")
        return FakeResponse(json.dumps(fake_work(42)).encode())

    monkeypatch.setattr("scripts.backfill_openalex.urlopen", fake_urlopen)
    work = fetch_openalex_work("10.1000/xyz")
    assert work is not None
    assert work["cited_by_count"] == 42


def test_fetch_openalex_work_404_returns_none(monkeypatch):
    from urllib.error import HTTPError

    def fake_urlopen(request, timeout=15.0):
        raise HTTPError("https://api.openalex.org/works/doi:missing", 404, "Not Found", Message(), None)

    monkeypatch.setattr("scripts.backfill_openalex.urlopen", fake_urlopen)
    assert fetch_openalex_work("10.1000/missing") is None


def test_fetch_openalex_work_network_error_returns_none(monkeypatch):
    def fake_urlopen(request, timeout=15.0):
        raise OSError("connection refused")

    monkeypatch.setattr("scripts.backfill_openalex.urlopen", fake_urlopen)
    assert fetch_openalex_work("10.1000/xyz") is None


def test_apply_work_sets_fields():
    item = {"slug": "a", "doi": "10.1000/xyz"}
    assert apply_work_to_item(item, fake_work(7)) is True
    assert item["cited_by_count"] == 7
    assert item["openalex_id"] == "https://openalex.org/W123456"
    assert not item.get("openalex_not_found")


def test_apply_work_none_marks_not_found():
    item = {"slug": "a", "doi": "10.1000/missing"}
    assert apply_work_to_item(item, None) is True
    assert item["openalex_not_found"] is True
    assert "cited_by_count" not in item


def test_apply_work_idempotent_no_change():
    item = {"slug": "a", "doi": "10.1000/xyz", "cited_by_count": 7, "openalex_id": "https://openalex.org/W123456"}
    assert apply_work_to_item(item, fake_work(7)) is False


def test_apply_work_none_idempotent_no_change():
    item = {"slug": "a", "doi": "10.1000/missing", "openalex_not_found": True}
    assert apply_work_to_item(item, None) is False


def test_backfill_skips_items_without_doi(monkeypatch):
    monkeypatch.setattr("scripts.backfill_openalex.fetch_openalex_work", lambda doi: fake_work(1))
    items = [{"slug": "a"}, {"slug": "b", "doi": "10.1000/xyz"}]
    fetched, changed = backfill(items, dry_run=False, sleep_s=0)
    assert fetched == 1
    assert changed == 1
    assert items[0].get("cited_by_count") is None
    assert items[1]["cited_by_count"] == 1


def test_backfill_skips_items_with_existing_metadata(monkeypatch):
    def boom(doi):
        raise AssertionError("should not fetch")

    monkeypatch.setattr("scripts.backfill_openalex.fetch_openalex_work", boom)
    items = [{"slug": "a", "doi": "10.1000/x", "openalex_id": "https://openalex.org/W1", "cited_by_count": 3}]
    fetched, changed = backfill(items, dry_run=False, sleep_s=0)
    assert fetched == 0
    assert changed == 0


def test_backfill_refresh_refetches_existing(monkeypatch):
    monkeypatch.setattr("scripts.backfill_openalex.fetch_openalex_work", lambda doi: fake_work(9))
    items = [{"slug": "a", "doi": "10.1000/x", "openalex_id": "https://openalex.org/W1", "cited_by_count": 3}]
    fetched, changed = backfill(items, dry_run=False, refresh=True, sleep_s=0)
    assert fetched == 1
    assert changed == 1
    assert items[0]["cited_by_count"] == 9


def test_backfill_dry_run_does_not_mutate(monkeypatch):
    monkeypatch.setattr("scripts.backfill_openalex.fetch_openalex_work", lambda doi: fake_work(5))
    items = [{"slug": "a", "doi": "10.1000/xyz"}]
    fetched, changed = backfill(items, dry_run=True, sleep_s=0)
    assert fetched == 1
    assert changed == 0
    assert "cited_by_count" not in items[0]
