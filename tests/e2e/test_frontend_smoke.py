"""P0 frontend smoke tests: CSP, console errors, same-origin 404s, key widgets."""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import pytest

pytestmark = pytest.mark.e2e

PAGES = [
    "/",
    "/start-here/",
    "/compliance/",
    "/markets/",
    "/data/",
    "/search/?q=aml",
    "/graph/",
    "/review/",
    "/study/",
    "/diagnostic/",
    "/concepts/kyc/",
    "/compliance/research/aml-1/",
    "/data/learn/data-engineering-basics/",
    "/knowledge/glossary/",
    "/404.html",
]

# Known P1 regressions. Keep this list explicit and tied to the item that removes it.
ALLOWED_404 = [
    (re.compile(r"/favicon\.ico$"), "P1 favicon"),
    (re.compile(r"_(?:400|800)w\.(?:svg|webp|png|jpe?g)$"), "P1 responsive images"),
]


def allowed_404(url: str) -> str | None:
    path = urlparse(url).path
    for pattern, label in ALLOWED_404:
        if pattern.search(path):
            return label
    return None


def _visit(page, base: str, path: str) -> list[str]:
    errors: list[str] = []
    page.add_init_script("try{localStorage.setItem('acacia_onboarding_seen','1')}catch(e){}")

    def on_console(msg):
        if msg.type != "error":
            return
        location = (msg.location or {}).get("url", "")
        if allowed_404(location):
            return
        # External analytics/images may be unreachable in CI; only CSP/refusal
        # messages for those are our problem.
        if location.startswith(("http://", "https://")) and not location.startswith(base):
            if "Content Security Policy" not in msg.text and "Refused to" not in msg.text:
                return
        errors.append(f"console: {msg.text} ({location})")

    def on_pageerror(exc):
        errors.append(f"pageerror: {exc}")

    def on_response(resp):
        if not resp.url.startswith(base) or resp.status < 400:
            return
        label = allowed_404(resp.url)
        if label:
            return
        errors.append(f"response {resp.status}: {resp.url}")

    def on_requestfailed(req):
        if not req.url.startswith(base):
            return
        errors.append(f"requestfailed: {req.url} ({req.failure})")

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.on("response", on_response)
    page.on("requestfailed", on_requestfailed)
    page.goto(base + path, wait_until="load", timeout=30000)
    page.wait_for_timeout(800)
    return errors


@pytest.mark.parametrize("path", PAGES)
def test_page_has_no_runtime_errors(page, base_url, path):
    errors = _visit(page, base_url, path)
    assert not errors, f"{path}\n" + "\n".join(errors)


def test_graph_renders(page, base_url):
    errors = _visit(page, base_url, "/graph/")
    page.wait_for_selector("#cy canvas", timeout=20000)
    assert not errors, "\n".join(errors)


def test_review_dashboard_populates(page, base_url):
    errors = _visit(page, base_url, "/review/")
    page.wait_for_function("document.getElementById('stat-due').textContent.trim() !== ''")
    assert not errors, "\n".join(errors)


def test_diagnostic_loads_questions(page, base_url):
    errors = _visit(page, base_url, "/diagnostic/")
    page.wait_for_selector("#diagnostic-list > *", timeout=15000)
    assert not errors, "\n".join(errors)


def test_quiz_payload_is_valid_json(page, base_url):
    errors = _visit(page, base_url, "/data/learn/designing-data-platform/")
    payload = page.eval_on_selector("[data-quiz]", "el => JSON.parse(el.dataset.quiz)")
    assert payload["questions"], "quiz payload is empty"
    assert not errors, "\n".join(errors)


def test_review_badge_skips_fetch_without_local_state(page, base_url):
    fetched: list[str] = []
    page.on(
        "request",
        lambda req: fetched.append(req.url)
        if re.search(r"/static/(review_concepts|flashcard_index)\.json$", req.url)
        else None,
    )
    errors = _visit(page, base_url, "/compliance/research/aml-1/")
    assert fetched == [], f"unexpected review-state fetch: {fetched}"
    assert not errors, "\n".join(errors)


def test_sqljs_assets_are_self_hosted(page, base_url):
    errors = _visit(page, base_url, "/data/learn/sql-for-data-engineers/")
    html = page.content()
    assert "cdn.jsdelivr.net/npm/sql.js" not in html
    assert "unpkg.com/sql.js" not in html
    assert not errors, "\n".join(errors)
