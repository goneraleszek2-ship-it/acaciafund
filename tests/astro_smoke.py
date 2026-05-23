#!/usr/bin/env python3
"""Smoke tests for the Astro build output."""

from pathlib import Path
import sys


BASE = Path(__file__).parent.parent / "web" / "dist"


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ✓ {msg}")
    else:
        print(f"  ✗ {msg}")
        raise SystemExit(1)


def read(path: str) -> str:
    return (BASE / path).read_text(encoding="utf-8")


def main() -> int:
    check((BASE / "index.html").is_file(), "Home page exists")
    check((BASE / "blog/index.html").is_file(), "Blog index exists")
    check((BASE / "course/index.html").is_file(), "Course page exists")
    check((BASE / "learn/index.html").is_file(), "Learn page exists")
    check((BASE / "about/index.html").is_file(), "About page exists")
    check((BASE / "contact/index.html").is_file(), "Contact page exists")
    home = read("index.html")
    check("AcaciaFund" in home, "Home page has brand")
    check("Daily research portfolio" in home or "Daily synthesis" in home, "Home page has product copy")
    check("Latest syntheses" in home or "Latest synthesis" in home, "Home page has latest section")
    check("Bayesian update" in read("learn/index.html"), "Learn page includes Bayes demo")
    check("lesson-01-intro" in read("learn/index.html"), "Learn index lists lessons")
    check("registry" in home.lower(), "Home page references registry metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
