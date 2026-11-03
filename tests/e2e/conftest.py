"""Shared fixtures for the Playwright P0 frontend smoke tests."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("pytest_playwright")

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def base_url():
    """Use BASE_URL when set (production), otherwise serve the local dist."""
    configured = os.environ.get("BASE_URL")
    if configured:
        yield configured.rstrip("/")
        return

    if not (ROOT / "dist").is_dir():
        pytest.skip("dist/ not built; run python3 build.py first")

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "serve_dist.py"), "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(url + "/", timeout=1).close()
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("serve_dist.py did not start")

    yield url
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
