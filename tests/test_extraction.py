"""Contract tests for core/extraction.py (Tier 5.2 structured extraction)."""

from core.content import Content
from core.extraction import (
    MAX_VARIABLES,
    attach_extraction,
    extract_from_item,
    extract_key_variables,
    extract_prisma_trail,
)


def _body(*paragraphs: str) -> str:
    return "".join(f"<p>{p}</p>" for p in paragraphs)


def test_percentage_variable():
    kv = extract_key_variables("<p>The model reached an accuracy of 92.4% on the held-out set.</p>")
    assert any(v["metric"] == "accuracy" and v["value"] == "92.4%" for v in kv)
    assert all("accuracy" in v["name"].lower() for v in kv if v["metric"] == "accuracy")


def test_decimal_variable():
    kv = extract_key_variables("<p>R-squared was 0.87 against the validation cohort.</p>")
    assert any(v["metric"] == "r2" and v["value"] == "0.87" for v in kv)


def test_pvalue_variable():
    kv = extract_key_variables("<p>The effect was significant, p < 0.05, across all strata.</p>")
    assert any(v["metric"] == "p_value" and "0.05" in v["value"] for v in kv)


def test_sample_size_variable():
    kv = extract_key_variables("<p>The study screened n = 1,234 records in total.</p>")
    assert any(v["metric"] == "sample_size" and v["value"] == "n = 1,234" for v in kv)


def test_sample_of_pattern():
    kv = extract_key_variables("<p>A sample of 500 transactions was audited.</p>")
    assert any(v["metric"] == "sample_size" and v["value"] == "n = 500" for v in kv)


def test_bare_numbers_not_extracted():
    assert extract_key_variables("<p>Page 12 of section 3 covers 2026 trends.</p>") == []


def test_metric_without_value_not_extracted():
    assert extract_key_variables("<p>The reported accuracy was later disputed in court.</p>") == []


def test_evidence_sentence_captured():
    kv = extract_key_variables("<p>First sentence. Latency dropped to 30 ms per record. Final one.</p>")
    match = [v for v in kv if v["metric"] == "latency"]
    assert match and "Latency dropped to 30 ms per record" in match[0]["evidence"]


def test_implausible_value_rejected():
    # 999 is not a plausible precision decimal and not a percentage here
    assert extract_key_variables("<p>Precision 999 led to no change.</p>") == []


def test_max_variables_capped():
    parts = []
    for i in range(MAX_VARIABLES + 5):
        parts.append(f"<p>Wave {i}: accuracy of {60 + i}.1% was recorded.</p>")
    kv = extract_key_variables(_body(*parts))
    assert len(kv) <= MAX_VARIABLES


def test_html_tags_stripped():
    kv = extract_key_variables("<p>AUC of <strong>0.94</strong> was reported.</p>")
    assert any(v["metric"] == "auc" and v["value"] == "0.94" for v in kv)


def test_prisma_trail_extracted():
    body = _body(
        "We identified 1,245 candidate studies.",
        "After screening 1,245 abstracts, we excluded 312 and assessed 933 full texts.",
        "A final set of 47 studies was included in the synthesis.",
    )
    trail = extract_prisma_trail(body)
    assert trail["identified"] == 1245
    assert trail["screened"] == 1245
    assert trail["excluded"] == 312
    assert trail["included"] == 47


def test_prisma_absent_returns_empty():
    assert extract_prisma_trail("<p>No screening process is described here.</p>") == {}


def test_extract_from_item_empty_body():
    item = Content(slug="a/b", title="t", pillar="aml", content_type="research")
    assert extract_from_item(item) == {}


def test_extract_from_item_attaches_data():
    item = Content(
        slug="aml/research/sample",
        title="t",
        pillar="aml",
        content_type="research",
        body_html="<p>Accuracy of 88.0% was reached with p < 0.05.</p>",
    )
    data = extract_from_item(item)
    assert data["key_variables"]
    assert data["prisma"] == {}


def test_attach_extraction_by_slug_matches():
    item = Content(slug="aml/research/sample", title="t", pillar="aml", content_type="research")
    pre = {"key_variables": [{"metric": "auc", "name": "AUC", "value": "0.9", "evidence": "e"}], "prisma": {}}
    attached = attach_extraction([item], slug_extraction={"aml/research/sample": pre})
    assert attached == 1
    assert item.extraction_data is not None
    assert item.extraction_data["key_variables"][0]["value"] == "0.9"


def test_attach_extraction_computes_when_no_map():
    item = Content(
        slug="aml/research/sample",
        title="t",
        pillar="aml",
        content_type="research",
        body_html="<p>Throughput of 1,500 tps was sustained.</p>",
    )
    attached = attach_extraction([item])
    assert attached == 1
    assert item.extraction_data is not None
    assert item.extraction_data["key_variables"][0]["metric"] == "throughput"


def test_attach_extraction_clears_missing():
    item = Content(slug="aml/research/plain", title="t", pillar="aml", content_type="research")
    attached = attach_extraction([item])
    assert attached == 0
    assert item.extraction_data is None
