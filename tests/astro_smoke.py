#!/usr/bin/env python3
"""Smoke tests for the Astro build output."""

from pathlib import Path
import sys


BASE = Path(__file__).parent.parent / "dist"


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
    check((BASE / "research/index.html").is_file(), "Research index exists")
    check((BASE / "learn/index.html").is_file(), "Learn page exists")
    check((BASE / "knowledge/index.html").is_file(), "Knowledge page exists")
    check((BASE / "search/index.html").is_file(), "Search page exists")
    home = read("index.html")
    check("AcaciaFund" in home, "Home page has brand")
    check("Continue Learning" in home, "Home page has continue learning section")
    check("Research" in home, "Home page has research section")
    learn = read("learn/index.html")
    check("Learning Hub" in learn, "Learn page has title")
    check("pillar-progress-section" in learn, "Learn page has pillar progress")
    check("review-due" in learn, "Learn page has review due section")
    check("Flashcards" in learn or "Knowledge Check" in learn or "lesson-status" in learn, "Learn page lists lessons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
