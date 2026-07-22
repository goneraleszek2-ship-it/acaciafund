"""Tests for generate_learn_modules.py"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_learn_modules import (
    AUTO_MODULE_PROMPT,
    MODULES,
    auto_generate_from_ontology,
    generate_module_body,
    main,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_ontology():
    """Create a mock OntologyManager with 5 concepts across 3 pillars."""
    from core.ontology import Concept

    ontology = MagicMock()
    ontology.concepts = [
        Concept(
            id="pyspark",
            label="PySpark",
            pillar="data-engineering",
            category="foundations",
            description="Distributed data processing with PySpark",
        ),
        Concept(
            id="kyc",
            label="Know Your Customer",
            pillar="aml",
            category="foundations",
            description="KYC compliance procedures",
        ),
        Concept(
            id="volatility",
            label="Volatility Analysis",
            pillar="stock",
            category="market-analysis",
            description="Measuring and modeling volatility",
        ),
        Concept(
            id="data-lake",
            label="Data Lake Architecture",
            pillar="data-engineering",
            category="architecture",
            description="Data lake design principles",
        ),
        Concept(
            id="sar",
            label="Suspicious Activity Reports",
            pillar="aml",
            category="regulations",
            description="SAR filing requirements",
        ),
    ]
    return ontology


@pytest.fixture
def empty_registry():
    """A registry dict with no content."""
    return {"content": []}


@pytest.fixture
def sample_registry_with_learn():
    """A registry with 2 existing learn modules."""
    return {
        "content": [
            {
                "slug": "data-engineering/learn/pyspark",
                "content_type": "learn",
                "title": "Existing PySpark",
                "pillar": "data-engineering",
            },
            {
                "slug": "aml/learn/kyc",
                "content_type": "learn",
                "title": "Existing KYC",
                "pillar": "aml",
            },
        ]
    }


# ── TestGenerateModuleBody ────────────────────────────────────────────────


class TestGenerateModuleBody:
    """Tests for generate_module_body()."""

    def test_with_valid_module(self) -> None:
        module = {
            "sections": [
                {"heading": "Intro", "content": "<p>First section</p>"},
                {"heading": "Advanced", "content": "<p>Second section</p>"},
            ]
        }
        result = generate_module_body(module)
        assert "<h2>Intro</h2>" in result
        assert "<p>First section</p>" in result
        assert "<h2>Advanced</h2>" in result
        assert "<p>Second section</p>" in result

    def test_with_empty_sections(self) -> None:
        module = {"sections": []}
        result = generate_module_body(module)
        assert result == ""

    def test_section_heading_rendered(self) -> None:
        module = {
            "sections": [
                {"heading": "Core Concepts", "content": "<p>Content</p>"}
            ]
        }
        result = generate_module_body(module)
        assert "<h2>Core Concepts</h2>" in result

    def test_content_rendered(self) -> None:
        module = {
            "sections": [
                {"heading": "Core Concepts", "content": "<p>Detailed content here</p>"}
            ]
        }
        result = generate_module_body(module)
        assert result.index("<h2>Core Concepts</h2>") < result.index("<p>Detailed content here</p>")


# ── TestAutoGeneratePrompt ───────────────────────────────────────────────


class TestAutoGeneratePrompt:
    """Tests for AUTO_MODULE_PROMPT template formatting."""

    def test_prompt_format(self) -> None:
        prompt = AUTO_MODULE_PROMPT.format(
            concept_label="PySpark",
            concept_id="pyspark",
            pillar="data-engineering",
            description="Distributed data processing",
            category="foundations",
            relations="category: foundations",
        )
        assert "Concept: PySpark (pyspark)" in prompt
        assert "Pillar: data-engineering" in prompt
        assert "Description: Distributed data processing" in prompt
        assert "Category: foundations" in prompt
        assert "Relations: category: foundations" in prompt

    def test_prompt_with_empty_relations(self) -> None:
        prompt = AUTO_MODULE_PROMPT.format(
            concept_label="Test",
            concept_id="test-concept",
            pillar="aml",
            description="Test description",
            category="reference",
            relations="none",
        )
        assert "Relations: none" in prompt


# ── TestAutoGenerateFromOntology ─────────────────────────────────────────


class TestAutoGenerateFromOntology:
    """Tests for auto_generate_from_ontology()."""

    def test_returns_empty_when_all_have_modules(self, mock_ontology: MagicMock) -> None:
        registry = {
            "content": [
                {"slug": "data-engineering/learn/pyspark", "content_type": "learn"},
                {"slug": "aml/learn/kyc", "content_type": "learn"},
                {"slug": "stock/learn/volatility", "content_type": "learn"},
                {"slug": "data-engineering/learn/data-lake", "content_type": "learn"},
                {"slug": "aml/learn/sar", "content_type": "learn"},
            ]
        }
        new_slugs = auto_generate_from_ontology(mock_ontology, registry)
        assert new_slugs == []

    def test_generates_modules_for_missing_concepts(
        self, mock_ontology: MagicMock, empty_registry: dict
    ) -> None:
        new_slugs = auto_generate_from_ontology(mock_ontology, empty_registry)
        assert len(new_slugs) == 5
        assert "data-engineering/learn/pyspark" in new_slugs
        assert "aml/learn/kyc" in new_slugs
        assert "stock/learn/volatility" in new_slugs
        assert "data-engineering/learn/data-lake" in new_slugs
        assert "aml/learn/sar" in new_slugs

    def test_max_new_limit(self, mock_ontology: MagicMock, empty_registry: dict) -> None:
        new_slugs = auto_generate_from_ontology(mock_ontology, empty_registry, max_new=1)
        assert len(new_slugs) == 1

    def test_uses_llm_client_when_provided(
        self, mock_ontology: MagicMock, empty_registry: dict
    ) -> None:
        llm_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps({
            "title": "LLM Generated Module",
            "description": "Generated by LLM",
            "difficulty": "intermediate",
            "tags": ["generated"],
            "sections": [
                {"heading": "LLM Section", "content": "<p>LLM content</p>"}
            ],
            "flashcards": [
                {"front": "Q?", "back": "A"}
            ],
            "bloom_questions": [
                {"question": "Test?", "choices": ["A", "B"], "correct_index": 0, "explanation": "E"}
            ],
        })
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        llm_client.chat.completions.create.return_value = mock_response

        new_slugs = auto_generate_from_ontology(
            mock_ontology, empty_registry, llm_client=llm_client, max_new=2
        )

        assert len(new_slugs) == 2
        assert llm_client.chat.completions.create.call_count == 2

    def test_deterministic_fallback(self, mock_ontology: MagicMock, empty_registry: dict) -> None:
        new_slugs = auto_generate_from_ontology(mock_ontology, empty_registry)

        assert len(new_slugs) == 5
        first = next(i for i in empty_registry["content"] if i["slug"] == new_slugs[0])
        assert "Understanding" in first["title"]
        assert first["auto_generated"] is True
        assert first["concept_enriched"] is True
        assert first["author"] == "AcaciaFund"

    def test_deterministic_fallback_has_correct_structure(
        self, mock_ontology: MagicMock, empty_registry: dict
    ) -> None:
        new_slugs = auto_generate_from_ontology(mock_ontology, empty_registry)

        assert len(new_slugs) > 0
        item = empty_registry["content"][0]
        assert "slug" in item
        assert "title" in item
        assert "pillar" in item
        assert "content_type" in item
        assert "tags" in item
        assert "description" in item
        assert "difficulty" in item
        assert "body_html" in item
        assert "bloom_questions" in item
        assert "flashcards" in item
        assert "prerequisites" in item
        assert "author" in item
        assert "created_at" in item
        assert "updated_at" in item
        assert "date_str" in item
        assert "auto_generated" in item
        assert "concept_enriched" in item
        assert "concept_id" in item

    def test_skips_slug_already_in_content(
        self, mock_ontology: MagicMock
    ) -> None:
        registry = {
            "content": [
                {"slug": "data-engineering/learn/pyspark", "content_type": "research"},
                {"slug": "data-engineering/learn/kyc", "content_type": "learn"},
            ]
        }
        new_slugs = auto_generate_from_ontology(mock_ontology, registry)

        # pyspark: in existing_slugs (as research, not learn), so should still be generated
        # kyc: in existing_learn_slugs, so skipped
        # volatility, data-lake, sar: generated
        # But wait - pyspark slug matches existing_slugs set, so the code does:
        #   if slug in existing_slugs:
        #       continue
        # So pyspark is skipped too
        assert "data-engineering/learn/pyspark" not in new_slugs
        assert "aml/learn/kyc" not in new_slugs


# ── TestMain ─────────────────────────────────────────────────────────────


class TestMain:
    """Integration-level tests for main()."""

    def test_hand_authored_modules_created(self, tmp_path: Path) -> None:
        reg_path = tmp_path / "registry.json"
        reg_path.write_text(json.dumps({"content": []}))
        nonexistent = tmp_path / "nonexistent.json"

        with patch("scripts.generate_learn_modules.REGISTRY_PATH", reg_path):
            with patch("scripts.generate_learn_modules.ONTOLOGY_PATH", nonexistent):
                with patch("scripts.generate_learn_modules.sys.argv", ["script"]):
                    main()

        registry = json.loads(reg_path.read_text())
        slugs = {item["slug"] for item in registry["content"]}
        for module in MODULES:
            assert module["slug"] in slugs, f"Missing: {module['slug']}"

    def test_skips_existing_modules(self, tmp_path: Path) -> None:
        existing_slug = MODULES[0]["slug"]
        reg_path = tmp_path / "registry.json"
        initial_content = [
            {
                "slug": existing_slug,
                "title": "Original Keep Title",
                "content_type": "learn",
                "pillar": MODULES[0]["pillar"],
                "tags": [],
                "description": "original",
                "difficulty": "beginner",
                "body_html": "<h2>existing</h2>",
                "bloom_questions": [],
                "flashcards": [],
                "prerequisites": [],
            }
        ]
        reg_path.write_text(json.dumps({"content": initial_content}))
        nonexistent = tmp_path / "nonexistent.json"

        with patch("scripts.generate_learn_modules.REGISTRY_PATH", reg_path):
            with patch("scripts.generate_learn_modules.ONTOLOGY_PATH", nonexistent):
                with patch("scripts.generate_learn_modules.sys.argv", ["script"]):
                    main()

        registry = json.loads(reg_path.read_text())
        slugs = [item["slug"] for item in registry["content"]]
        assert slugs.count(existing_slug) == 1
        original = next(i for i in registry["content"] if i["slug"] == existing_slug)
        assert original["title"] == "Original Keep Title"

    def test_auto_generate_with_infer(self, tmp_path: Path) -> None:
        import os as _os
        import sys as _sys
        import types as _types

        reg_path = tmp_path / "registry.json"
        reg_path.write_text(json.dumps({"content": []}))
        mock_onto = MagicMock()
        from core.ontology import Concept

        mock_onto.concepts = [
            Concept(
                id="test-concept",
                label="Test Concept",
                pillar="data-engineering",
                category="foundations",
            ),
        ]

        mock_llm = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps({
            "title": "LLM Module",
            "description": "LLM generated",
            "difficulty": "intermediate",
            "tags": ["test"],
            "sections": [{"heading": "Intro", "content": "<p>Content</p>"}],
            "flashcards": [{"front": "Q?", "back": "A"}],
            "bloom_questions": [
                {"question": "Q?", "choices": ["A", "B"], "correct_index": 0, "explanation": "E"}
            ],
        })
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_llm.chat.completions.create.return_value = mock_response

        fake_openai_mod = _types.ModuleType("openai")
        setattr(fake_openai_mod, "OpenAI", MagicMock(return_value=mock_llm))
        _sys.modules["openai"] = fake_openai_mod

        with patch("scripts.generate_learn_modules.REGISTRY_PATH", reg_path):
            with patch("scripts.generate_learn_modules.ONTOLOGY_PATH", reg_path):
                with patch(
                    "scripts.generate_learn_modules.OntologyManager.load",
                    return_value=mock_onto,
                ):
                    with patch("scripts.generate_learn_modules.sys.argv", ["script", "--infer"]):
                        with patch.dict(_os.environ, {"NVIDIA_API_KEY": "fake-key"}):
                            main()

        registry = json.loads(reg_path.read_text())
        items = [i for i in registry["content"] if "test-concept" in i.get("slug", "")]
        assert len(items) == 1
        assert items[0]["title"] == "LLM Module"

    def test_auto_generate_skipped_without_infer(self, tmp_path: Path) -> None:
        reg_path = tmp_path / "registry.json"
        reg_path.write_text(json.dumps({"content": []}))
        mock_onto = MagicMock()
        mock_onto.concepts = []

        logged_lines: list[str] = []

        def tracking_info(msg: str, *args, **kwargs) -> None:
            logged_lines.append(str(msg))

        with patch("scripts.generate_learn_modules.REGISTRY_PATH", reg_path):
            with patch("scripts.generate_learn_modules.ONTOLOGY_PATH", reg_path):
                with patch(
                    "scripts.generate_learn_modules.OntologyManager.load",
                    return_value=mock_onto,
                ):
                    with patch("scripts.generate_learn_modules.sys.argv", ["script"]):
                        with patch(
                            "scripts.generate_learn_modules.logger.info",
                            tracking_info,
                        ):
                            main()

        assert any("Skipping" in line for line in logged_lines)
