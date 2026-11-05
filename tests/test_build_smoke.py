"""Post-build smoke tests: verify dist/ output structure and content."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestDistStructure:
    """Verify the dist/ directory has the expected structure."""

    def test_dist_exists(self, dist_dir):
        assert dist_dir.is_dir()

    def test_compliance_index(self, dist_dir):
        assert (dist_dir / "compliance" / "index.html").exists()

    def test_markets_index(self, dist_dir):
        assert (dist_dir / "markets" / "index.html").exists()

    def test_data_index(self, dist_dir):
        assert (dist_dir / "data" / "index.html").exists()

    def test_aml_redirect_exists(self, dist_dir):
        assert (dist_dir / "aml" / "index.html").exists()

    def test_no_aml_research_content(self, dist_dir):
        aml_research = dist_dir / "aml" / "research"
        assert not aml_research.exists(), (
            "aml/research/ should not exist — content should be at compliance/research/"
        )

    def test_no_aml_learn_content(self, dist_dir):
        aml_learn = dist_dir / "aml" / "learn"
        assert not aml_learn.exists(), (
            "aml/learn/ should not exist — content should be at compliance/learn/"
        )

    def test_compliance_has_content_dirs(self, dist_dir):
        compliance = dist_dir / "compliance"
        for subdir in ["knowledge", "learn", "research"]:
            d = compliance / subdir
            assert d.exists(), f"dist/compliance/{subdir}/ not found"
            html_files = list(d.rglob("*.html"))
            assert len(html_files) > 0, f"dist/compliance/{subdir}/ is empty"


class TestComplianceContent:
    """Verify compliance pillar content renders correctly."""

    def test_pillar_page_has_heading(self, dist_dir):
        content = (dist_dir / "compliance" / "index.html").read_text(encoding="utf-8")
        assert "Compliance" in content

    def test_pillar_page_has_diagnostic_cta(self, dist_dir):
        content = (dist_dir / "compliance" / "index.html").read_text(encoding="utf-8")
        assert 'class="diagnostic-cta' in content
        assert "/diagnostic/" in content

    def test_pillar_page_has_side_rail(self, dist_dir):
        content = (dist_dir / "compliance" / "index.html").read_text(encoding="utf-8")
        assert "pillar-rail" in content
        assert "pillar_rail" in content and ".js" in content

    def test_learn_page_has_sm2_cta_and_prereq_banner(self, dist_dir):
        learn_pages = list((dist_dir / "compliance" / "learn").rglob("index.html"))
        assert len(learn_pages) > 0
        for page in learn_pages:
            content = page.read_text(encoding="utf-8")
            if "data-add-to-queue" in content:
                assert "data-flashcard-ids" in content, f"{page} CTA missing card ids"
                break
        else:
            raise AssertionError("No compliance learn page rendered the SM-2 CTA")

    def test_study_page_has_dashboard_sidebar(self, dist_dir):
        content = (dist_dir / "study" / "index.html").read_text(encoding="utf-8")
        assert "study-dashboard" in content
        assert "study_dashboard" in content and ".js" in content
        assert "side-week" in content and "side-upcoming" in content and "side-weak" in content

    def test_mobile_tabbar_present_on_all_layouts(self, dist_dir):
        content = (dist_dir / "study" / "index.html").read_text(encoding="utf-8")
        assert 'class="mobile-tabbar"' in content
        assert "data-tab-badge" in content


    def test_knowledge_pages_exist(self, dist_dir):
        knowledge = dist_dir / "compliance" / "knowledge"
        pages = list(knowledge.iterdir())
        assert len(pages) >= 1, f"Expected >=1 knowledge pages, got {len(pages)}"

    def test_learn_pages_exist(self, dist_dir):
        learn = dist_dir / "compliance" / "learn"
        pages = list(learn.iterdir())
        assert len(pages) >= 10, f"Expected >=10 learn pages, got {len(pages)}"

    def test_research_pages_exist(self, dist_dir):
        research = dist_dir / "compliance" / "research"
        pages = list(research.iterdir())
        assert len(pages) >= 5, f"Expected >=5 research pages, got {len(pages)}"


class TestAccessibility:
    def test_nav_marks_current_pillar(self, dist_dir):
        content = (dist_dir / "compliance" / "index.html").read_text(encoding="utf-8")
        assert 'href="/compliance/" aria-current="page"' in content

    def test_newsletter_input_has_label(self, dist_dir):
        content = (dist_dir / "knowledge" / "glossary" / "index.html").read_text(encoding="utf-8")
        assert 'for="newsletter-email"' in content
        assert 'id="newsletter-email"' in content

    def test_graph_has_noscript_fallback(self, dist_dir):
        content = (dist_dir / "graph" / "index.html").read_text(encoding="utf-8")
        assert "<noscript>" in content
        assert "/letters/" in content


class TestSeoMetadata:
    """Verify canonical, social metadata, and P1 asset fixes."""

    def test_homepage_has_canonical(self, dist_dir):
        content = (dist_dir / "index.html").read_text(encoding="utf-8")
        assert '<link rel="canonical" href="https://www.acaciafund.org/">' in content

    def test_content_page_has_canonical_and_social_tags(self, dist_dir):
        page = dist_dir / "compliance" / "research" / "aml-1" / "index.html"
        content = page.read_text(encoding="utf-8")
        assert '<link rel="canonical" href="https://www.acaciafund.org/compliance/research/aml-1/">' in content
        assert '<meta property="og:type" content="article">' in content
        assert '<meta property="og:url" content="https://www.acaciafund.org/compliance/research/aml-1/">' in content
        assert 'name="twitter:card"' in content

    def test_favicon_and_manifest_exist(self, dist_dir):
        assert (dist_dir / "favicon.ico").exists()
        assert (dist_dir / "static" / "site.webmanifest").exists()

    def test_svg_images_do_not_emit_width_srcset(self, dist_dir):
        pages = [
            dist_dir / "compliance" / "research" / "aml-1" / "index.html",
            dist_dir / "data" / "research" / "2027-data-engineering-predictions" / "index.html",
        ]
        for page in pages:
            if page.exists():
                content = page.read_text(encoding="utf-8")
                assert "_400w.svg" not in content
                assert "_800w.svg" not in content

    def test_no_public_page_has_multiple_h1(self, dist_dir):
        import re

        offenders = []
        for page in dist_dir.rglob("*.html"):
            if "admin" in page.parts:
                continue
            count = len(re.findall(r"<h1\b", page.read_text(encoding="utf-8", errors="ignore"), re.IGNORECASE))
            if count > 1:
                offenders.append(str(page.relative_to(dist_dir)))
        assert not offenders, f"pages with multiple h1: {offenders[:10]}"

    def test_thin_tag_pages_are_noindex(self, dist_dir):
        tag_pages = list((dist_dir / "tags").glob("*/index.html"))
        assert tag_pages, "expected tag pages"
        thin = [
            p for p in tag_pages
            if '<meta name="robots" content="noindex,follow">' in p.read_text(encoding="utf-8")
        ]
        assert thin, "expected at least one thin tag page marked noindex"


class TestSitemap:
    """Verify sitemap uses URL-form paths."""

    def test_sitemap_exists(self, dist_dir):
        assert (dist_dir / "sitemap.xml").exists()

    def test_sitemap_has_compliance_urls(self, dist_dir):
        content = (dist_dir / "sitemap.xml").read_text(encoding="utf-8")
        assert "/compliance/" in content

    def test_sitemap_no_aml_pillar_urls(self, dist_dir):
        content = (dist_dir / "sitemap.xml").read_text(encoding="utf-8")
        import re
        # Check that /aml/ is never used as a pillar prefix
        # Valid: /compliance/research/aml/ (article named "aml")
        # Invalid: /aml/research/foo/ (using internal key as path segment)
        bad = re.findall(r"<loc>https?://[^<]*/aml/(?:research|learn|knowledge|signals)/[^<]*</loc>", content)
        assert bad == [], f"Sitemap contains /aml/ pillar-prefixed URLs: {bad}"

    def test_sitemap_covers_generated_routes(self, dist_dir):
        content = (dist_dir / "sitemap.xml").read_text(encoding="utf-8")
        for route in ("/concepts/", "/journeys/", "/learning-paths/", "/design-system/"):
            assert f"{route}" in content, f"sitemap missing {route}"
        assert content.count("<loc>") > 2000

    def test_sitemap_excludes_admin_and_redirects(self, dist_dir):
        content = (dist_dir / "sitemap.xml").read_text(encoding="utf-8")
        assert "<loc>https://www.acaciafund.org/admin/" not in content
        assert "/404.html" not in content
        assert "<loc>https://www.acaciafund.org/contact/</loc>" not in content

    def test_robots_disallows_admin(self, dist_dir):
        content = (dist_dir / "robots.txt").read_text(encoding="utf-8")
        assert "Disallow: /admin/" in content


class TestFeed:
    """Verify feed.xml uses URL-form paths."""

    def test_feed_exists(self, dist_dir):
        assert (dist_dir / "feed.xml").exists()

    def test_feed_has_compliance_urls(self, dist_dir):
        content = (dist_dir / "feed.xml").read_text(encoding="utf-8")
        assert "/compliance/" in content


class TestLlmsTxt:
    """Verify llms.txt uses URL-form paths."""

    def test_llms_txt_exists(self, dist_dir):
        assert (dist_dir / "llms.txt").exists()

    def test_llms_txt_has_compliance_urls(self, dist_dir):
        content = (dist_dir / "llms.txt").read_text(encoding="utf-8")
        assert "/compliance/" in content

    def test_llms_txt_no_raw_aml_slugs(self, dist_dir):
        content = (dist_dir / "llms.txt").read_text(encoding="utf-8")
        import re
        # Check no /aml/research or /aml/learn references
        bad = re.findall(r"acaciafund\.org/aml/(?:research|learn)/", content)
        assert bad == [], f"llms.txt has raw aml slugs: {bad}"


class TestBuildMetadata:
    """Verify build metadata is generated correctly."""

    def test_build_meta_exists(self, dist_dir):
        assert (dist_dir / "build-meta.json").exists()

    def test_build_meta_is_valid_json(self, dist_dir):
        import json
        content = (dist_dir / "build-meta.json").read_text(encoding="utf-8")
        data = json.loads(content)
        assert "page_count" in data or "total_pages" in data
