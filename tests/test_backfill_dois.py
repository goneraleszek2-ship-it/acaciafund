"""Contract tests for scripts/backfill_dois.py."""

from scripts.backfill_dois import backfill, derive_doi_for_item
from scripts.knowledge_ingester import arxiv_doi_for_id


def test_derive_doi_from_arxiv_abs_url():
    item = {"slug": "a", "source_url": "http://arxiv.org/abs/2607.05307v1"}
    assert derive_doi_for_item(item) == "10.48550/arXiv.2607.05307"


def test_derive_doi_from_arxiv_pdf_url():
    item = {"slug": "a", "source_url": "https://arxiv.org/pdf/2607.05141"}
    assert derive_doi_for_item(item) == "10.48550/arXiv.2607.05141"


def test_no_doi_for_non_arxiv_url():
    item = {"slug": "a", "source_url": "https://news.ycombinator.com/item?id=123"}
    assert derive_doi_for_item(item) is None


def test_existing_doi_not_overwritten():
    item = {"slug": "a", "source_url": "http://arxiv.org/abs/2607.05307", "doi": "10.1000/keep"}
    assert derive_doi_for_item(item) is None


def test_no_source_url_means_no_doi():
    assert derive_doi_for_item({"slug": "a"}) is None


def test_backfill_dry_run_does_not_mutate():
    items = [
        {"slug": "a", "source_url": "https://arxiv.org/abs/2607.05307"},
        {"slug": "b"},
    ]
    assert backfill(items, dry_run=True) == 1
    assert items[0].get("doi") is None


def test_backfill_apply_sets_dois():
    items = [
        {"slug": "a", "source_url": "https://arxiv.org/abs/2607.05307"},
        {"slug": "b"},
    ]
    assert backfill(items, dry_run=False) == 1
    assert items[0]["doi"] == "10.48550/arXiv.2607.05307"
    assert "doi" not in items[1]


def test_arxiv_doi_strips_version_suffix():
    assert arxiv_doi_for_id("2608.04832v1") == "10.48550/arXiv.2608.04832"
    assert arxiv_doi_for_id("2608.04832") == "10.48550/arXiv.2608.04832"
    assert arxiv_doi_for_id("hep-th/9901001v2") == "10.48550/arXiv.hep-th/9901001"


def test_arxiv_doi_empty_or_whitespace():
    assert arxiv_doi_for_id("") == ""
    assert arxiv_doi_for_id("   ") == ""
