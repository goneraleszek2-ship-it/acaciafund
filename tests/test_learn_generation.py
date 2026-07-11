"""Tests for learn module generation and Phase 3 features."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_learn_modules import MODULES, generate_module_body


class TestModuleDefinitions:
    """Test the module definition data structures."""

    def test_modules_list_not_empty(self):
        assert len(MODULES) >= 8

    def test_all_pillars_covered(self):
        pillars = {m["pillar"] for m in MODULES}
        assert "data-engineering" in pillars
        assert "aml" in pillars
        assert "stock" in pillars

    def test_each_module_has_required_fields(self):
        required = {"slug", "title", "pillar", "tags", "description", "sections", "bloom_questions"}
        for module in MODULES:
            missing = required - set(module.keys())
            assert not missing, f"Module {module.get('slug', '?')} missing: {missing}"

    def test_slug_format(self):
        for module in MODULES:
            slug = module["slug"]
            assert "/" in slug, f"Slug {slug} should contain /"
            assert slug.endswith("/" + slug.split("/")[-1])

    def test_no_slug_duplicates(self):
        slugs = [m["slug"] for m in MODULES]
        assert len(slugs) == len(set(slugs))

    def test_sections_are_nonempty(self):
        for module in MODULES:
            assert len(module["sections"]) >= 2, f"{module['slug']} needs >= 2 sections"
            for section in module["sections"]:
                assert "heading" in section
                assert "content" in section
                assert len(section["content"]) > 50

    def test_bloom_questions_cover_levels(self):
        for module in MODULES:
            levels = {q["level"] for q in module["bloom_questions"]}
            assert len(levels) >= 3, f"{module['slug']} needs >= 3 bloom levels, got {levels}"

    def test_flashcards_present(self):
        for module in MODULES:
            assert len(module.get("flashcards", [])) >= 2


class TestModuleBodyGeneration:
    """Test HTML body generation from module definitions."""

    def test_generate_body_returns_html(self):
        body = generate_module_body(MODULES[0])
        assert "<h2>" in body
        assert "<p>" in body
        assert "<code" in body

    def test_generate_body_includes_all_sections(self):
        module = MODULES[0]
        body = generate_module_body(module)
        for section in module["sections"]:
            assert section["heading"] in body

    def test_generate_body_code_blocks(self):
        # Find a module with code blocks
        for module in MODULES:
            body = generate_module_body(module)
            if "<code" in body:
                assert body.count("<code") >= 1
                return
        pytest.skip("No modules with code blocks")


class TestRegistryIntegration:
    """Test that generated modules appear in registry."""

    def test_registry_loads(self):
        registry_path = Path(__file__).parent.parent / "registry.json"
        assert registry_path.exists()

    def test_generated_modules_in_registry(self):
        registry_path = Path(__file__).parent.parent / "registry.json"
        with open(registry_path) as f:
            registry = json.load(f)
        slugs = {item["slug"] for item in registry["content"]}
        for module in MODULES:
            assert module["slug"] in slugs, f"{module['slug']} not in registry"

    def test_generated_modules_have_learn_type(self):
        registry_path = Path(__file__).parent.parent / "registry.json"
        with open(registry_path) as f:
            registry = json.load(f)
        for module in MODULES:
            item = next(i for i in registry["content"] if i["slug"] == module["slug"])
            assert item["content_type"] == "learn"
            assert item["pillar"] == module["pillar"]
            assert len(item.get("bloom_questions", [])) >= 3
