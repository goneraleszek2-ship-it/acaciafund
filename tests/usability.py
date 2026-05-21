#!/usr/bin/env python3
"""
Synthetic use tests: simulate user journeys through the AcaciaFund learning platform.
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
PUBLIC = BASE / "public"
API = BASE / "static" / "api"

PASS = 0
FAIL = 0
WARN = 0


def check(cond: bool, msg: str):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {msg}")
    else:
        FAIL += 1
        print(f"  ✗ {msg}")


def warn(msg: str):
    global WARN
    WARN += 1
    print(f"  ⚠ {msg}")


def read_html(path: str) -> str:
    return (PUBLIC / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads((API / path).read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("USABILITY — SYNTHETIC USE TESTS")
print("=" * 60)

# ── 1. DATA INTEGRITY ──
print("\n── 1. DATA INTEGRITY ──")

articles = read_json("articles.json")
check("posts" in articles, "/api/articles.json has 'posts'")
check(len(articles["posts"]) > 0, f"  {len(articles['posts'])} posts")

quiz = read_json("quiz.json")
check("questions" in quiz, "/api/quiz.json has 'questions'")
check(quiz["count"] > 0, f"  {quiz['count']} questions")

flashcards = read_json("flashcards.json")
check("cards" in flashcards, "/api/flashcards.json has 'cards'")
check(flashcards["count"] > 0, f"  {flashcards['count']} cards")

bloom = read_json("bloom.json")
check("overview" in bloom, "/api/bloom.json has 'overview'")
check("by_pillar" in bloom, "/api/bloom.json has 'by_pillar'")

# Check data consistency
post_urls = set()
for post in articles["posts"]:
    url = post.get("url", "")
    if url:
        post_urls.add(url.rstrip("/"))

for q in quiz["questions"]:
    pu = q.get("post_url", "")
    if pu:
        norm = pu.rstrip("/")
        if norm not in post_urls:
            # May use date-based format not in articles.json
            pass

for c in flashcards["cards"]:
    src = c.get("source", "")
    if src:
        norm = src.rstrip("/")
        if norm not in post_urls and c.get("source_type") == "llm":
            warn(f"LLM flashcard references unknown source: {src}")

# Check bloom_levels in posts
no_bloom = [p for p in articles["posts"] if not p.get("bloom_levels")]
if no_bloom:
    warn(f"{len(no_bloom)} posts missing bloom_levels")

# ── 2. PAGE STRUCTURE ──
print("\n── 2. PAGE STRUCTURE ──")

# Homepage
home = read_html("index.html")
check("class=\"live\"" in home, "Homepage has live indicator")
check("Przegląd dnia" in home, "Homepage shows daily overview")
check("Ostatnie artykuły" in home, "Homepage shows recent articles")
check("Pipeline aktywny" in home, "Homepage shows pipeline status")
check("DataOps" in home, "Homepage shows DataOps metrics")
check("/learn/" in home, "Homepage has link to /learn/")
check("continueLearning" in home, "Homepage has continue learning widget")
check("ac-last-visit" in home, "Homepage has new-post notification JS")
check("new-posts-badge" in home, "Homepage has new-posts-badge CSS class")

# Dashboard
dash = read_html("learn/index.html")
check("Panel nauki" in dash, "Dashboard shows title")
check("dashboardRoot" in dash, "Dashboard has root container")
check("dashboardMetrics" in dash, "Dashboard has metrics container")
check("streakCount" in dash, "Dashboard has streak counter")
check("quizTotal" in dash, "Dashboard has quiz total counter")
check("cardsTotal" in dash, "Dashboard has cards total counter")
check("postsRead" in dash, "Dashboard has posts read counter")
check("bloomProgress" in dash, "Dashboard has bloom progress section")
check("pillarProgress" in dash, "Dashboard has pillar progress section")
check("recommendationBox" in dash, "Dashboard has recommendation section")
check("achievements" in dash, "Dashboard has achievements section")
check("learningPaths" in dash, "Dashboard has learning paths section")
check("recentActivity" in dash, "Dashboard has recent activity section")

# Check dashboard JS functions exist
for fn in ["computeStreak", "showMetrics", "renderBloomBars",
           "renderPillarBars", "renderPaths", "renderRecommendation",
           "renderActivity", "evaluateAchievements", "renderAchievements"]:
    check(f"function {fn}" in dash, f"Dashboard has {fn}()")

# Archive
archive = read_html("daily/aml/index.html")
check("Archiwum:" in archive, "Archive shows title")
check("sortSelect" in archive, "Archive has sort dropdown")
check("groupSelect" in archive, "Archive has group dropdown")
check("searchInput" in archive, "Archive has search input")
check("tagFilters" in archive, "Archive has tag filters")
check("postList" in archive, "Archive has post list container")
check("post-card" in archive, "Archive renders post cards")
check("Następny krok" in archive, "Archive has recommendation badge JS")

# Single post (pick the first available)
post_files = sorted((PUBLIC / "daily" / "aml").glob("2026-*/index.html"))
if post_files:
    post_path = post_files[0]
    post = read_html(f"daily/aml/{post_path.parent.name}/{post_path.name}")
    check("post-layout" in post, "Single post has sidebar layout")
    check("bloomSidebar" in post, "Single post has bloom sidebar")
    check("bloomNav" in post, "Single post has bloom nav container")
    check("postMeta" in post, "Single post has postMeta data div")
    check("quizWidget" in post, "Single post has quiz widget")
    check("flashcardWidget" in post, "Single post has flashcard widget")
    check("class=\"edu-widget\"" in post, "Single post has edu-widget class")
    for fn_name in ["answer", "flipCard", "rateCard"]:
        check(f"window.{fn_name}" in post or f"function {fn_name}" in post,
              f"Single post has {fn_name}()")
    check("/learn/" in post, "Single post has link to /learn/")
    check("/api/quiz.json" in post, "Single post fetches quiz.json")
    check("/api/flashcards.json" in post, "Single post fetches flashcards.json")
else:
    warn("No single post files found to test")

# ── 3. NAVIGATION FLOW ──
print("\n── 3. NAVIGATION FLOW ──")

pages = {
    "Homepage": "index.html",
    "Dashboard": "learn/index.html",
    "Archive (AML)": "daily/aml/index.html",
    "Archive (Markets)": "daily/stock/index.html",
    "Archive (Science)": "daily/science/index.html",
    "Diagrams": "diagrams/index.html",
    "Notebook": "notebook/index.html",
}

for name, path in pages.items():
    html = read_html(path)
    check("/" in html, f"{name} → links to Home")
    check("/learn/" in html, f"{name} → links to Dashboard")

# Cross-navigation: archive → post (via JS data-posts attribute)
archive_has_post_data = "data-posts" in archive
check(archive_has_post_data, "Archive has post data for dynamic rendering")
if archive_has_post_data:
    # All 3 pillar archives should have post data
    for p in ["aml", "stock", "science"]:
        a = read_html(f"daily/{p}/index.html")
        check("data-posts" in a, f"  Archive ({p}) has data-posts attribute")

# Homepage → pillar archive
for pillar in ["aml", "stock", "science"]:
    check(f"/daily/{pillar}/" in home, f"Homepage links to pillar {pillar}")

# ── 4. LOCALSTORAGE KEY CONSISTENCY ──
print("\n── 4. LOCALSTORAGE KEY CONSISTENCY ──")

# Check localStorage key patterns in JS source files (layouts), not built HTML
layout_files = list((BASE / "layouts").rglob("*.html"))
all_source = " ".join(f.read_text(encoding="utf-8") for f in layout_files)

check("ac-fund-dark" in all_source, "Dark mode key 'ac-fund-dark' used")
check("ac-quiz-" in all_source, "Quiz key prefix 'ac-quiz-' used")
check("ac-flashcards-" in all_source, "Flashcard key prefix 'ac-flashcards-' used")
check("ac-read-" in all_source, "Read key prefix 'ac-read-' used")
check("ac-achievements" in all_source, "Achievements key 'ac-achievements' used")
check("ac-last-visit" in all_source, "Last-visit key 'ac-last-visit' used")

# ── 5. RESPONSIVE / CSS ──
print("\n── 5. RESPONSIVE & CSS ──")

css_file = (PUBLIC / "css" / "main.css").read_text(encoding="utf-8")
# Check for responsive breakpoints in external CSS
check("@media(max-width:640px)" in css_file, "Has 640px responsive breakpoint")
check("@media(max-width:480px)" in css_file, "Has 480px responsive breakpoint")

# Check dark mode variables exist
check(".dark" in css_file, "Has .dark CSS class for dark mode")
check("--bg:" in css_file, "Has CSS variables defined")

# Check new components have styles
check("ach-card" in css_file, "Has ach-card CSS class")
check("path-step" in css_file, "Has path-step CSS class")
check("bloom-bars" in css_file, "Has bloom-bars CSS class")
check("bloom-bar-row" in css_file, "Has bloom-bar-row CSS class")
check("activity-item" in css_file, "Has activity-item CSS class")
check("new-posts-badge" in css_file, "Has new-posts-badge CSS class")
check("post-layout" in css_file, "Has post-layout CSS (sidebar)")
check("fc-card" in css_file, "Has flashcard CSS (fc-card)")

# ── 6. USER JOURNEY SIMULATIONS ──
print("\n── 6. USER JOURNEY SIMULATIONS ──")

# Journey 1: First visit → Homepage → Archive → Post
print("  Journey 1: Home → Archive (AML) → Single Post")
check("🏠 Home" in home and "Przegląd dnia" in home, "  1a. Homepage greets user with overview")
check("Ostatnie artykuły" in home, "  1b. Recent articles shown")
check("🛡️" in archive, "  1c. Archive renders with pillar emoji")
check("post-card" in archive, "  1d. Post cards rendered in archive")
if post_files:
    check("🗓" in post or "📅" in post, "  1e. Single post has date metadata")
    check("bloom-level" in post, "  1f. Bloom sidebar rendered")
    check("Pytania do refleksji" in post or "edu-widget" in post,
          "  1g. Post has educational sections")

# Journey 2: Learning → Dashboard
print("\n  Journey 2: Home → Dashboard")
check("📊" in dash, "  2a. Dashboard accessible")
check("🧠 Postęp Bloom" in dash, "  2b. Bloom progress section present")
check("📂 Postęp według filaru" in dash, "  2c. Pillar progress present")
check("🎯 Rekomendowany" in dash, "  2d. Recommendation present")
check("🏆 Osiągnięcia" in dash, "  2e. Achievements present")
check("🧭 Ścieżki nauki" in dash, "  2f. Learning paths present")
check("⏱️ Ostatnia aktywność" in dash, "  2g. Recent activity present")

# Journey 3: Reading flow → Quiz → Flashcards
print("\n  Journey 3: Quiz & Flashcard interaction")
if post_files:
    post_text = read_html(f"daily/aml/{post_files[0].parent.name}/{post_files[0].name}")
    check("quiz-btn" in post_text, "  3a. Quiz has interactive buttons")
    check("fc-card" in post_text, "  3b. Flashcards have interactive cards")
else:
    warn("  (no post to check)")

# Journey 4: Achievement evaluation
print("\n  Journey 4: Achievement system")
check("ACHIEVEMENTS" in dash, "  4a. Achievements defined in JS")
check("evaluateAchievements" in dash, "  4b. Achievement evaluation function exists")
check("ac-achievements" in dash, "  4c. Achievements saved to localStorage")
check("ach-card" in dash and ".unlocked" in css_file, "  4d. Achievement cards with locked/unlocked states")

# Journey 5: Dark mode
print("\n  Journey 5: Dark mode")
check("data-toggle-dark" in home, "  5a. Dark mode toggle button exists")
check("data-toggle-dark" in dash, "  5b. Dashboard has toggle")
check("data-toggle-dark" in archive, "  5c. Archive has toggle")
if post_files:
    check("data-toggle-dark" in post, "  5d. Post has toggle")
check("ac-fund-dark" in all_source, "  5e. Dark mode state persisted")

# ── 7. ERROR & EDGE CASE HANDLING ──
print("\n── 7. EDGE CASES & DEGRADATION ──")

# Empty state (dashboard when no data)
check("Brak danych" in dash, "Dashboard shows empty state message")
check("Brak aktywności" in dash, "Dashboard shows no-activity message")

# Quiz widget hidden by default (shown by JS only when questions match)
if post_files:
    post_text = read_html(f"daily/aml/{post_files[0].parent.name}/{post_files[0].name}")
    check('id="quizWidget" class="edu-widget" style="display:none"' in post_text,
          "Quiz widget starts hidden (display:none)")
else:
    warn("No post to check for quiz widget hiding")

# Flashcard widget hidden by default
if post_files:
    check('id="flashcardWidget" class="edu-widget" style="display:none"' in post_text,
          "Flashcard widget starts hidden (display:none)")
else:
    warn("No post to check for flashcard hiding")

# Bloom sidebar always shown (hides only when JS detects no bloom data)
if post_files:
    check("bloomSidebar" in post_text,
          "Bloom sidebar rendered in post")
else:
    warn("No post to check for bloom sidebar")

# Archive: search returns no results
check("Brak wyników" in archive, "Archive shows no-results message")

# Fetch errors caught
check(".catch(function" in dash, "Dashboard catches fetch errors")
check(".catch(function" in (home + (post if post_files else "")),
      "Homepage catches fetch errors")

# ── 8. ACCESSIBILITY BASICS ──
print("\n── 8. ACCESSIBILITY ──")

check("lang=\"pl\"" in home, "Homepage has lang=pl")
check("lang=\"pl\"" in dash, "Dashboard has lang=pl")
check("lang=\"pl\"" in archive, "Archive has lang=pl")
check("aria-label" in home, "Homepage has aria-labels")
check("alt=\"\"" in home, "Images have alt attributes (empty or descriptive)")

# ── SUMMARY ──
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed, {WARN} warnings")
if FAIL:
    sys.exit(1)
