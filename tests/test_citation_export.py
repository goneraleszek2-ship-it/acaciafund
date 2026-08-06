"""Contract tests for the citation export partial (BibTeX + RIS)."""

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from core.content import Content


def render_citation(item):
    env = Environment(loader=FileSystemLoader("templates"), undefined=StrictUndefined)
    env.filters["striptags"] = lambda v: str(v)
    tmpl = env.get_template("partials/citation_export.j2")
    return tmpl.render(content=item)


def make_item(**kw):
    base = dict(
        slug="markets/research/factor-investing",
        title="Factor Investing: A Survey",
        author="AcaciaFund",
        date_str="2026-03-15",
        source_url="https://arxiv.org/abs/2603.00001",
        doi="10.48550/arXiv.2603.00001",
    )
    base.update(kw)
    return Content.from_dict(base)


def test_bibtex_renders_with_doi():
    html = render_citation(make_item())
    assert "@misc" in html
    assert "factor-investing" in html
    assert "10.48550/arXiv.2603.00001" in html
    assert "Cite this synthesis" in html


def test_ris_renders():
    html = render_citation(make_item())
    assert "TY  - GEN" in html
    assert "DO  - 10.48550/arXiv.2603.00001" in html
    assert "UR  - https://arxiv.org/abs/2603.00001" in html


def test_doi_link_present():
    html = render_citation(make_item())
    assert "https://doi.org/10.48550/arXiv.2603.00001" in html


def test_no_export_without_doi_or_url():
    html = render_citation(make_item(doi=None, source_url=None))
    assert "Cite this synthesis" not in html


def test_bibtex_uses_year_from_date_str():
    html = render_citation(make_item())
    assert "year = { 2026 }" in html
