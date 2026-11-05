#!/usr/bin/env python3
"""Serve dist/ locally with the Cloudflare `_headers` policy applied.

Used by the Playwright smoke tests so CSP violations are reproducible locally
instead of relying on Cloudflare's edge.
"""

from __future__ import annotations

import argparse
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
HEADERS_FILE = DIST / "_headers"

mimetypes.add_type("application/wasm", ".wasm")


def load_headers() -> list[tuple[str, dict[str, str]]]:
    rules: list[tuple[str, dict[str, str]]] = []
    current: dict[str, str] | None = None
    for raw in HEADERS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("/"):
            current = {}
            rules.append((line.strip(), current))
        elif current is not None and ":" in line:
            key, value = line.strip().split(":", 1)
            current[key.strip()] = value.strip()
    return rules


def matches(pattern: str, path: str) -> bool:
    if pattern.endswith("*"):
        return path.startswith(pattern[:-1])
    return path == pattern or path == pattern.rstrip("/") + "/"


class Handler(SimpleHTTPRequestHandler):
    headers_rules = load_headers()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def end_headers(self) -> None:
        applied: dict[str, str] = {}
        for pattern, headers in self.headers_rules:
            if matches(pattern, self.path.split("?", 1)[0]):
                applied.update(headers)
        for key, value in applied.items():
            self.send_header(key, value)
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve dist/ with _headers policy")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving {DIST} at http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
