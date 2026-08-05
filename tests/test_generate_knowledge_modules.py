"""Guard tests for scripts/generate_knowledge_modules.py modules.

Every hand-authored knowledge module must carry the SQI-relevant fields
(bloom_questions, citations, source_breakdown) and a minimal body, so the
SQI gate (>= 0.65 for all items) cannot silently regress when modules are
added or edited.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "generate_knowledge_modules.py"


def _load_modules() -> list[dict]:
    spec = importlib.util.spec_from_file_location("generate_knowledge_modules", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MODULES


@pytest.fixture(scope="module")
def modules() -> list[dict]:
    return _load_modules()


def test_all_modules_have_sections(modules: list[dict]) -> None:
    for module in modules:
        assert len(module["sections"]) >= 3, f"{module['slug']}: needs >= 3 sections"


def test_all_modules_have_bloom_questions(modules: list[dict]) -> None:
    for module in modules:
        qs = module.get("bloom_questions", [])
        assert len(qs) >= 3, f"{module['slug']}: needs >= 3 bloom questions"
        assert {"level", "question"} <= set(qs[0]), f"{module['slug']}: bad bloom question shape"


def test_all_modules_have_citations(modules: list[dict]) -> None:
    for module in modules:
        cites = module.get("citations", [])
        assert len(cites) >= 3, f"{module['slug']}: needs >= 3 citations"
        for cite in cites:
            assert {"title", "url", "type"} <= set(cite), f"{module['slug']}: bad citation shape"
            assert cite["url"].startswith("http"), f"{module['slug']}: citation URL not absolute"


def test_all_modules_have_source_breakdown(modules: list[dict]) -> None:
    for module in modules:
        sb = module.get("source_breakdown", {})
        assert sum(sb.values()) >= 3, f"{module['slug']}: source_breakdown must total >= 3"


def test_all_modules_have_valid_slugs(modules: list[dict]) -> None:
    slugs = [module["slug"] for module in modules]
    assert len(slugs) == len(set(slugs)), "duplicate module slugs"
    for slug in slugs:
        parts = slug.split("/")
        assert len(parts) == 3 and parts[1] == "knowledge", f"{slug}: not a knowledge slug"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
