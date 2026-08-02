"""Tests for core/bloom.py — Bloom taxonomy classification, quiz + flashcard generation."""

from core.bloom import (
    _build_content_question,
    _build_domain_type_question,
    _build_factoid_question,
    _build_source_tier_question,
    _extract_bigrams,
    bloom_verb,
    classify_bloom_level,
    generate_flashcards,
    generate_quiz_questions,
    level_index,
    level_label_en,
)

# ── classify_bloom_level ──
#
# Contract:
#   classify_bloom_level(article: dict) -> str (one of the 6 Bloom levels)
#   - arXiv + create keyword  → "create"
#   - gov/edu + evaluate keyword → "evaluate"
#   - arXiv + apply keyword → "apply"
#   - keyword match → that level
#   - points >= 200 → "evaluate"; >= 50 → "understand"; > 0 → "remember"
#   - default → "understand"


class TestClassifyBloomLevel:
    def test_arxiv_create_keyword(self):
        article = {"title": "A novel approach to option pricing", "url": "https://arxiv.org/abs/2401.0001"}
        assert classify_bloom_level(article) == "create"

    def test_gov_evaluate_keyword(self):
        article = {"title": "New regulatory framework for stablecoins", "url": "https://www.sec.gov"}
        assert classify_bloom_level(article) == "evaluate"

    def test_arxiv_apply_keyword(self):
        article = {"title": "Implementing a market-making system", "url": "https://arxiv.org/abs/2401.0002"}
        assert classify_bloom_level(article) == "apply"

    def test_analyze_keyword(self):
        article = {"title": "An analysis of market microstructure", "url": "https://example.com/x", "points": 0}
        assert classify_bloom_level(article) == "analyze"

    def test_remember_keyword(self):
        article = {"title": "Apple launches new earnings transparency report", "url": "https://example.com/x", "points": 0}
        assert classify_bloom_level(article) == "remember"

    def test_points_evaluate(self):
        article = {"title": "Some neutral title about markets", "url": "https://example.com/x", "points": 250}
        assert classify_bloom_level(article) == "evaluate"

    def test_points_understand(self):
        article = {"title": "Some neutral title about markets", "url": "https://example.com/x", "points": 60}
        assert classify_bloom_level(article) == "understand"

    def test_points_remember(self):
        article = {"title": "Some neutral title about markets", "url": "https://example.com/x", "points": 10}
        assert classify_bloom_level(article) == "remember"

    def test_default_understand(self):
        article = {"title": "Notes on the weekend", "url": "https://example.com/x", "points": 0}
        assert classify_bloom_level(article) == "understand"

    def test_missing_points_default(self):
        article = {"title": "Notes on the weekend", "url": "https://example.com/x"}
        assert classify_bloom_level(article) == "understand"


# ── bloom_verb / level_index / level_label_en ──


class TestBloomHelpers:
    def test_bloom_verb_known(self):
        assert bloom_verb("create") == "creating"
        assert bloom_verb("analyze") == "analyzing"

    def test_bloom_verb_unknown(self):
        assert bloom_verb("nope") == "reviewing"

    def test_level_index_order(self):
        assert level_index("remember") == 0
        assert level_index("create") == 5

    def test_level_index_unknown(self):
        assert level_index("nope") == -1

    def test_level_label_en(self):
        assert level_label_en("remember") == "Remembering"
        assert level_label_en("evaluate") == "Evaluating"

    def test_level_label_unknown(self):
        assert level_label_en("nope") == "Nope"


# ── _extract_bigrams ──
#
# Contract:
#   _extract_bigrams(title) -> list[str] of Capitalized Capitalized phrases
#   - requires both words capitalized, >= 4 chars, phrase >= 14 chars
#   - skips stop words and punctuation


class TestExtractBigrams:
    def test_extracts_capitalized_bigrams(self):
        bigrams = _extract_bigrams("Kubernetes Cluster Deployment and Docker Containers")
        assert "Kubernetes Cluster" in bigrams
        assert "Docker Containers" in bigrams

    def test_skips_lowercase_words(self):
        assert _extract_bigrams("how to deploy docker containers") == []

    def test_skips_short_words(self):
        assert _extract_bigrams("AI ML XKCD Sort Merge") == []

    def test_skips_stopwords(self):
        assert "What Next" not in _extract_bigrams("What Next Chapter")

    def test_single_word_title(self):
        assert _extract_bigrams("Kubernetes") == []


# ── generate_flashcards ──


class TestGenerateFlashcards:
    def test_returns_list_with_structure(self):
        cards = generate_flashcards(
            [{"title": "Kubernetes Cluster Deployment in Production"}], "data-engineering"
        )
        assert isinstance(cards, list)
        assert len(cards) <= 120
        for card in cards:
            for key in ("term", "definition", "pillar", "source", "source_type"):
                assert key in card

    def test_empty_articles(self):
        assert generate_flashcards([]) == []

    def test_unique_terms(self):
        cards = generate_flashcards(
            [{"title": "Kubernetes Cluster Deployment and Docker Containers"}], "data-engineering"
        )
        terms = [c["term"] for c in cards]
        assert len(terms) == len(set(terms))


# ── generate_quiz_questions ──


class TestGenerateQuizQuestions:
    def test_returns_questions_with_bloom_level(self):
        articles = [
            {"title": "A novel approach to volatility forecasting", "url": "https://arxiv.org/abs/2401.0001"},
            {"title": "An analysis of order book dynamics", "url": "https://example.com/order-book"},
        ]
        questions = generate_quiz_questions(articles, "Markets")
        assert isinstance(questions, list)
        assert all("bloom_level" in q and "question" in q for q in questions)

    def test_empty_articles(self):
        assert generate_quiz_questions([], "Markets") == []


# ── Individual question builders ──


class TestQuestionBuilders:
    def test_source_tier_question_arxiv(self):
        q = _build_source_tier_question({"url": "https://arxiv.org/abs/2401.0001"})
        assert q is not None
        assert q["correct"] == "High – academic source"
        assert q["bloom_level"] == "evaluate"

    def test_source_tier_question_community(self):
        q = _build_source_tier_question({"url": "https://github.com/foo/bar"})
        assert q is not None
        assert q["correct"] == "Low – community source"

    def test_source_tier_no_url(self):
        assert _build_source_tier_question({}) is None

    def test_domain_type_commercial(self):
        q = _build_domain_type_question({"url": "https://example.com/x"})
        assert q is not None
        assert q["correct"] == "Commercial"
        assert q["bloom_level"] == "understand"

    def test_domain_type_gov(self):
        q = _build_domain_type_question({"url": "https://example.gov/x"})
        assert q is not None
        assert q["correct"] == "Government"

    def test_factoid_question_with_number(self):
        sentence = "The company reported revenues of 12 billion dollars this year."
        q = _build_factoid_question(sentence, "Earnings report")
        assert q is not None
        assert q["type"] == "tf"
        assert q["correct"] is True

    def test_factoid_too_short(self):
        assert _build_factoid_question("Short.", "Earnings") is None

    def test_factoid_no_number(self):
        assert _build_factoid_question("The firm outlined a completely qualitative strategy shift today.", "X") is None

    def test_content_question_names(self):
        q = _build_content_question("Apple and Google earnings", ["Apple Inc", "Google Corp"], "Markets")
        assert q is not None
        assert q["type"] == "mc"
        assert q["correct"] in q["options"]

    def test_content_question_insufficient_names(self):
        assert _build_content_question("Title here", [], "Markets") is None
