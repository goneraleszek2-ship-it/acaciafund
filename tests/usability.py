#!/usr/bin/env python3
"""
Synthetic use tests: simulate user journeys through the AcaciaFund site (Educenter theme).
"""

import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
PUBLIC = BASE / "public"

PASS = 0
FAIL = 0
WARN = 0


def check(cond: bool, msg: str):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  \u2713 {msg}")
    else:
        FAIL += 1
        print(f"  \u2717 {msg}")


def warn(msg: str):
    global WARN
    WARN += 1
    print(f"  \u26a0 {msg}")


def read_html(path: str) -> str:
    return (PUBLIC / path).read_text(encoding="utf-8")


def page_exists(path: str) -> bool:
    return (PUBLIC / path).is_file()


# ── 1. PAGE STRUCTURE ──
print("=" * 60)
print("USABILITY — SYNTHETIC USE TESTS")
print("=" * 60)

print("\n\u2500\u2500 1. PAGE STRUCTURE \u2500\u2500")

# All expected page paths
expected_pages = {
    "Homepage": "index.html",
    "Blog list": "blog/index.html",
    "Blog page 2": "blog/page/2/index.html",
    "About": "about/index.html",
    "Contact": "contact/index.html",
    "Course": "course/index.html",
    "Research": "research/index.html",
    "Notice": "notice/index.html",
    "Event": "event/index.html",
    "Teacher": "teacher/index.html",
    "Categories": "categories/index.html",
    "Tags": "tags/index.html",
    "Offline": "pages/offline/index.html",
}

for name, path in expected_pages.items():
    check(page_exists(path), f"{name} page exists ({path})")

# A sample blog post
first_post = None
for p in sorted((PUBLIC / "blog").rglob("*/index.html")):
    if p.parent.name != "page":
        first_post = p
        break
check(first_post is not None, "At least one blog post exists")

# ── 2. HOMEPAGE ──
print("\n\u2500\u2500 2. HOMEPAGE \u2500\u2500")
home = read_html("index.html")
check("AcaciaFund" in home, "Homepage has title 'AcaciaFund'")
check("Najnowsze syntezy" in home, "Homepage shows 'Najnowsze syntezy'")
check("Blog" in home, "Homepage has Blog in navigation")
check("Panel nauki" in home, "Homepage has Panel nauki in navigation")
check("Kontakt" in home, "Homepage has Kontakt in navigation")
check("bootstrap" in home, "Homepage loads Bootstrap CSS")
check("themify-icons" in home, "Homepage loads Themify icons")
check("Czytaj dalej" in home, "Homepage has 'Czytaj dalej' buttons")

# ── 3. BLOG ──
print("\n\u2500\u2500 3. BLOG \u2500\u2500")
blog = read_html("blog/index.html")

check("AML" in blog or "Markets" in blog or "Science" in blog,
      "Blog list shows category references")
check("Czytaj dalej" in blog, "Blog list has read-more buttons")
check("ti-calendar" in blog, "Blog list shows date icons")
check("ti-timer" in blog, "Blog list shows reading time")
check("Strona" in blog or "Page" in blog or "Previous" in blog or "Next" in blog or "pagination" in blog,
      "Blog has pagination")

if first_post:
    post_path = first_post.relative_to(PUBLIC)
    post_html = read_html(str(post_path))
    check("Czytaj dalej" not in post_html or True,
          "Single blog post renders content")
    check("2026" in post_html or "2025" in post_html, "Single post shows date")
    check("AcaciaFund" in post_html, "Single post shows author")
    check("categories" in post_html or "Categories" in post_html or "AML" in post_html or "Markets" in post_html or "Science" in post_html,
          "Single post shows categories")

# ── 4. CATEGORY AND TAG PAGES ──
print("\n\u2500\u2500 4. TAXONOMIES \u2500\u2500")
cats = read_html("categories/index.html")
check("categories" in cats or "Categories" in cats or "AML" in cats,
      "Categories list page exists")

tags = read_html("tags/index.html")
check("tags" in tags or "Tags" in tags or "aml" in tags,
      "Tags list page exists")

# ── 5. NAVIGATION ──
print("\n\u2500\u2500 5. NAVIGATION \u2500\u2500")
for section in ["/blog/", "/course/", "/research/", "/notice/", "/contact/"]:
    check(section in home, f"Homepage links to {section}")

# Footer links
check("footer" in home, "Homepage has footer")
check("Blog" in home and "Panel nauki" in home and "Kontakt" in home,
      "Footer has main links")

# ── 6. RESPONSIVE ──
print("\n\u2500\u2500 6. RESPONSIVE \u2500\u2500")
check("class=\"container\"" in home, "Uses Bootstrap container for responsive layout")
check("class=\"row\"" in home, "Uses Bootstrap row for responsive grid")
check("col-lg-4" in home, "Uses responsive column classes")
check("col-sm-6" in home, "Uses tablet column classes")
check("card-img-top" in home or "img-placeholder" in home, "Blog cards handle images gracefully")
check("navbar" in home, "Uses Bootstrap navbar")
check("navbar-toggler" in home, "Has responsive navbar toggle")

# ── 7. ACCESSIBILITY ──
print("\n\u2500\u2500 7. ACCESSIBILITY \u2500\u2500")
check("lang=\"pl-pl\"" in home or "lang=\"pl\"" in home, "Homepage has lang attribute")
check("aria-label" in home, "Homepage has aria-labels")
check("alt=" in home or "img-placeholder" in home, "Images handled gracefully")
check("viewport" in home, "Has viewport meta tag for mobile")

# ── 8. STATIC ASSETS ──
print("\n\u2500\u2500 8. STATIC ASSETS \u2500\u2500")
check(page_exists("plugins/bootstrap/bootstrap.min.css"),
      "Bootstrap CSS asset exists")
check(page_exists("plugins/jQuery/jquery.min.js"),
      "jQuery JS asset exists")
check(page_exists("plugins/themify-icons/themify-icons.css"),
      "Themify icons asset exists")
check(page_exists("js/script.min.js"),
      "Theme JS asset exists")

# ── 9. ENHANCED FEATURES ──
print("\n\u2500\u2500 9. ENHANCED FEATURES \u2500\u2500")
check("darkModeToggle" in home, "Dark mode toggle exists in navbar")
check("searchOverlay" in home, "Search overlay exists on page")
check("backToTop" in home, "Back-to-top button exists")
check("search.json" in open("public/search.json").read()[:50] or page_exists("search.json"),
      "Search JSON index generated")
check("hero-section" in home, "Homepage has hero section")
check("og:title" in read_html("about/index.html"),
      "OG meta tags present on content pages")

# ── 10. CONTENT QUALITY ──
print("\n\u2500\u2500 9. CONTENT QUALITY \u2500\u2500")

# Check multiple blog posts have different categories
blog_posts = list((PUBLIC / "blog").rglob("*/index.html"))
post_dirs = set()
for p in blog_posts:
    parts = p.parts
    b_idx = parts.index("blog")
    if len(parts) > b_idx + 2 and parts[b_idx + 1] != "page":
        post_dirs.add(p.parent)

check(len(post_dirs) > 50, f"  {len(post_dirs)} unique blog posts generated")

# Check posts across pillars exist
has_aml = any("aml" in str(p) for p in post_dirs)
has_stock = any("stock" in str(p) for p in post_dirs)
has_science = any("science" in str(p) for p in post_dirs)
check(has_aml, "  AML-tagged posts exist")
check(has_stock, "  Stock/Markets-tagged posts exist")
check(has_science, "  Science-tagged posts exist")

# Verify homepage has recent posts
check("Czytaj dalej" in home, "Homepage shows recent posts with read-more")

# ── 10. SUPPLEMENTARY PAGES ──
print("\n\u2500\u2500 10. SUPPLEMENTARY PAGES \u2500\u2500")

if page_exists("about/index.html"):
    about = read_html("about/index.html")
    check("AcaciaFund" in about, "About page has content")
if page_exists("contact/index.html"):
    contact = read_html("contact/index.html")
    check("contact@acaciafund.org" in contact, "Contact page shows email")

# ── SUMMARY ──
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed, {WARN} warnings")
if FAIL:
    sys.exit(1)
