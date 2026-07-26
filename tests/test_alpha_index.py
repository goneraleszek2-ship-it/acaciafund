"""Tests for the alpha index generator (MathWorld-inspired A-Z browser)."""



from scripts.generate_alpha_index import _first_letter, _make_content, generate_alpha_index


class FakeContent:
    """Minimal content item for testing."""

    def __init__(self, title="", slug="", pillar="aml", content_type="knowledge",
                 description="", date_str="", tags=None):
        self.title = title
        self.slug = slug
        self.pillar = pillar
        self.content_type = content_type
        self.description = description
        self.date_str = date_str
        self.tags = tags or []
        self.body_html = ""
        self.source_breakdown = None
        self.sqi = 0.5
        self.created_at = None
        self.updated_at = None
        self.signals = {}
        self.contributors = None
        self.see_also = None
        self.explore_tools = None
        self.subject_classifications = None
        self.last_verified = None


class FakeRenderer:
    """Captures template calls instead of rendering."""

    def __init__(self):
        self.calls = []
        self._index = 0

    def render(self, template_name, **kw):
        self.calls.append((template_name, kw))
        page_path = kw.get("page_path", "letters/")
        self._index += 1
        return f"<html><!-- {template_name} {page_path} --></html>"


def test_first_letter():
    """_first_letter should handle various title formats."""
    assert _first_letter("Group") == "G"
    assert _first_letter("abstract algebra") == "A"
    assert _first_letter("3D Modeling") == "0-9"
    assert _first_letter("") == "?"
    assert _first_letter("_private") == "P"
    assert _first_letter("X-Ray") == "X"


def test_make_content():
    """_make_content should produce useful content objects."""
    c = _make_content("Test Title", "A test description")
    assert c.title == "Test Title"
    assert c.description == "A test description"
    assert c.slug == ""
    assert c.tags == []


def test_generate_alpha_index_creates_output(tmp_path):
    """generate_alpha_index should create /letters/ and /letters/{letter}/ pages."""
    items = [
        FakeContent("Group Theory", "aml/knowledge/group-theory", "aml"),
        FakeContent("Algebra", "aml/knowledge/algebra", "aml"),
        FakeContent("Beneficial Ownership", "aml/knowledge/beneficial-ownership", "aml"),
        FakeContent("Data Pipeline", "data-engineering/knowledge/data-pipeline", "data-engineering"),
        FakeContent("Market Microstructure", "stock/knowledge/market-microstructure", "stock"),
        FakeContent("Zero Knowledge Proof", "data-engineering/knowledge/zkp", "data-engineering"),
        FakeContent("3D Visualization", "data-engineering/knowledge/3d-viz", "data-engineering"),
    ]

    renderer = FakeRenderer()
    ctx_base = {
        "site_url": "https://example.com",
        "pillar_config": {
            "aml": {"label": "Compliance", "url": "compliance"},
            "stock": {"label": "Markets", "url": "markets"},
            "data-engineering": {"label": "Data", "url": "data"},
        },
    }

    count = generate_alpha_index(tmp_path, items, renderer.render, ctx_base,
                                  pillar_config=ctx_base["pillar_config"])

    # Should have generated pages for: A, B, D, G, M, Z, 0-9 + master index = 8
    assert count >= 7

    # Check master index exists
    assert (tmp_path / "letters" / "index.html").exists()

    # Check per-letter pages exist
    assert (tmp_path / "letters" / "a" / "index.html").exists()  # Algebra
    assert (tmp_path / "letters" / "b" / "index.html").exists()  # Beneficial Ownership
    assert (tmp_path / "letters" / "g" / "index.html").exists()  # Group Theory
    assert (tmp_path / "letters" / "digit" / "index.html").exists()  # 3D Visualization

    # Check master index rendering includes alphabet navigation
    master_html = (tmp_path / "letters" / "index.html").read_text()
    assert "alpha_index.j2" in master_html  # our fake renderer includes template name


def test_letter_page_content_in_context(tmp_path):
    """Per-letter pages should receive correct letter and entries in template context."""
    items = [
        FakeContent("Algebra", "aml/knowledge/algebra", "aml"),
        FakeContent("Applied Math", "aml/knowledge/applied-math", "aml"),
        FakeContent("Abstract Algebra", "aml/knowledge/abstract-algebra", "aml"),
    ]

    renderer = FakeRenderer()
    ctx_base = {
        "site_url": "https://example.com",
        "pillar_config": {},
    }

    generate_alpha_index(tmp_path, items, renderer.render, ctx_base)

    # Find the 'A' letter page call
    a_calls = [c for c in renderer.calls if c[1].get("current_letter") == "A"]
    assert len(a_calls) == 1

    call = a_calls[0]
    entries = call[1].get("entries", [])
    assert len(entries) == 3
    titles = [e["title"] for e in entries]
    assert "Algebra" in titles
    assert "Applied Math" in titles
    assert "Abstract Algebra" in titles

    # Titles should be sorted alphabetically
    assert titles == sorted(titles)


def test_letter_counts_correct(tmp_path):
    """Letter counts in master index should be accurate."""
    items = [
        FakeContent("Algebra", "aml/knowledge/a1", "aml"),
        FakeContent("Art", "aml/knowledge/a2", "aml"),
        FakeContent("Beta", "aml/knowledge/b1", "aml"),
        FakeContent("Balance", "aml/knowledge/b2", "aml"),
        FakeContent("Bond", "aml/knowledge/b3", "aml"),
    ]

    renderer = FakeRenderer()
    ctx_base = {"site_url": "https://example.com", "pillar_config": {}}

    generate_alpha_index(tmp_path, items, renderer.render, ctx_base)

    master_calls = [c for c in renderer.calls if c[1].get("current_letter") is None]
    assert len(master_calls) >= 1

    letter_counts = master_calls[0][1].get("letter_counts", {})
    assert letter_counts.get("A") == 2
    assert letter_counts.get("B") == 3


def test_empty_content(tmp_path):
    """Generator should handle empty content list gracefully."""
    renderer = FakeRenderer()
    ctx_base = {"site_url": "https://example.com", "pillar_config": {}}

    count = generate_alpha_index(tmp_path, [], renderer.render, ctx_base)
    assert count >= 1  # at least the master index page
    assert (tmp_path / "letters" / "index.html").exists()


def test_first_letter_edge_cases():
    """Edge cases for letter extraction."""
    assert _first_letter("  Spaces Before") == "S"
    assert _first_letter("___underscore") == "U"
    assert _first_letter("123abc") == "0-9"
    assert _first_letter("") == "?"
    assert _first_letter("A") == "A"
    assert _first_letter("z") == "Z"
