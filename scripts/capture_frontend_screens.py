#!/usr/bin/env python3
"""Capture side-by-side 390px/1280px screenshots of key frontend templates."""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = [
    ("home", "/"),
    ("start-here", "/start-here/"),
    ("pillar-compliance", "/compliance/"),
    ("research-article", "/compliance/research/aml-1/"),
    ("learn", "/data/learn/data-engineering-basics/"),
    ("glossary", "/knowledge/glossary/"),
    ("concept", "/concepts/kyc/"),
    ("search", "/search/?q=aml"),
    ("graph", "/graph/"),
    ("review", "/review/"),
]
VIEWPORTS = [(390, 844, "390"), (1280, 800, "1280")]


def start_server() -> tuple[subprocess.Popen, str]:
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
            return proc, url
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("serve_dist.py failed to start")


def composite(paths: list[Path], out: Path) -> None:
    images = [Image.open(p).convert("RGB") for p in paths]
    gap = 16
    width = sum(i.width for i in images) + gap * (len(images) - 1)
    height = max(i.height for i in images)
    canvas = Image.new("RGB", (width, height), "white")
    x = 0
    for image in images:
        canvas.paste(image, (x, 0))
        x += image.width + gap
    canvas.save(out)


def capture(base: str, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for name, path in TEMPLATES:
            shots = []
            for width, height, label in VIEWPORTS:
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                page.emulate_media(reduced_motion="reduce")
                page.goto(base + path, wait_until="load", timeout=30000)
                page.wait_for_timeout(1000)
                page.add_style_tag(
                    content="*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}"
                )
                shot = out / f"{name}-{label}.png"
                page.screenshot(path=str(shot), full_page=False)
                shots.append(shot)
                context.close()
            composite(shots, out / f"{name}.png")
            print(f"  {name}")
        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--base-url")
    args = parser.parse_args()
    proc = None
    base = args.base_url
    if not base:
        proc, base = start_server()
    try:
        capture(base.rstrip("/"), Path(args.out))
    finally:
        if proc:
            proc.terminate()
            proc.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
