"""Optional Pyodide smoke test. Slow and non-blocking: CDN + ~10 MB download."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


def test_pyodide_sandbox_runs(page, base_url):
    page.goto(base_url + "/data/learn/", wait_until="load", timeout=30000)
    sandbox = page.query_selector("[data-py-sandbox]")
    if sandbox is None:
        pytest.skip("no Pyodide sandbox on this build")
        return
    sandbox.query_selector("[data-py-run]").click()
    page.wait_for_function(
        "() => { const el = document.querySelector('[data-py-status]'); return el && el.textContent.trim().length > 0; }",
        timeout=120000,
    )
    assert "error" not in (sandbox.query_selector("[data-py-status]").inner_text().lower())
