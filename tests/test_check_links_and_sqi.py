"""Contract tests for scripts/check_links_and_sqi.py."""

import json

from scripts.check_links_and_sqi import (
    check_links,
    check_low_sqi,
    extract_internal_links,
)


def write_page(dist, rel_path, html):
    f = dist / rel_path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(html, encoding="utf-8")


def test_extract_internal_links_skips_assets_and_external(tmp_path):
    html = """
    <a href="/markets/research/a">A</a>
    <a href="/static/css/main.css">css</a>
    <a href="/images/logo.png">img</a>
    <a href="https://example.com/x">ext</a>
    <a href="/markets/research/a#section">anchored</a>
    <a href="/favicon.ico">fav</a>
    """
    links = extract_internal_links(html)
    assert "/markets/research/a" in links
    assert all("/static" not in link and "/images" not in link for link in links)
    assert "https://example.com/x" not in links
    assert "/favicon.ico" not in links


def test_check_links_no_broken(tmp_path):
    write_page(tmp_path, "index.html", '<a href="/markets/research/a">A</a>')
    write_page(tmp_path, "markets/research/a/index.html", "<h2>ok</h2>")
    write_page(tmp_path, "markets/research/b/index.html", '<a href="/">home</a>')
    assert check_links(tmp_path) == []


def test_check_links_finds_broken(tmp_path):
    write_page(tmp_path, "index.html", '<a href="/markets/research/missing">M</a>')
    write_page(tmp_path, "markets/research/a/index.html", "<h2>ok</h2>")
    broken = check_links(tmp_path)
    assert len(broken) == 1
    assert "/markets/research/missing" in broken[0]


def test_check_links_ignores_admin_and_tag_specials(tmp_path):
    write_page(
        tmp_path,
        "index.html",
        '<a href="/admin/quality">admin</a><a href="/tags/$foo">t</a><a href="/tags/abc">t2</a>',
    )
    write_page(tmp_path, "tags/abc/index.html", "<h2>ok</h2>")
    assert check_links(tmp_path) == []


def test_check_low_sqi_flags_below_threshold(tmp_path):
    write_page(tmp_path, "a/index.html", '<div data-sqi="0.80">a</div>')
    write_page(tmp_path, "b/index.html", '<div data-sqi="0.45">b</div>')
    write_page(tmp_path, "c/index.html", '<div data-sqi="0.66">c</div>')
    low = check_low_sqi(tmp_path, threshold=0.65)
    slugs = {item["file"] for item in low}
    assert slugs == {"b/index.html"}
    assert all(item["sqi"] < 0.65 for item in low)


def test_main_exit_zero_when_all_ok(tmp_path):
    write_page(tmp_path, "index.html", "<h2>home</h2>")
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "scripts/check_links_and_sqi.py", "--dist-dir", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads((tmp_path / "link-check-report.json").read_text())
    assert report["broken_count"] == 0


def test_main_exit_one_when_broken(tmp_path):
    write_page(tmp_path, "index.html", '<a href="/nope">x</a>')
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "scripts/check_links_and_sqi.py", "--dist-dir", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    report = json.loads((tmp_path / "link-check-report.json").read_text())
    assert report["broken_count"] == 1
