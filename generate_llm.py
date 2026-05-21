#!/usr/bin/env python3
"""
Optional LLM-powered enhancement of educational content.
Requires LLM_API_KEY env var (OpenAI-compatible API). Falls back gracefully if unset.
Usage: LLM_API_KEY=sk-... LLM_MODEL=gpt-4o-mini python3 generate_llm.py

Enhances quiz.json and flashcards.json with context-aware Q&A from article content.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
API_KEY = os.environ.get("LLM_API_KEY", "")
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
API_URL = os.environ.get("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
MAX_POSTS = int(os.environ.get("LLM_MAX_POSTS", "50"))
BATCH_SIZE = 5


def llm_complete(prompt: str, system: str = "") -> str | None:
    if not API_KEY:
        return None
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system or "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 2000,
    }).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [!] LLM call failed: {e}", file=sys.stderr)
        return None


def build_quiz_prompt(post: dict, articles: list[dict]) -> str:
    titles = "\n".join(f"- {a.get('title','?')}" for a in articles[:5])
    levels = post.get("bloom_levels", []) or ["understand"]
    return (
        f"Post: \"{post['title']}\" ({post['pillar']}, {post['date']})\n"
        f"Article titles:\n{titles}\n\n"
        f"Generate exactly {len(levels)} open-ended quiz questions in Polish, "
        f"one per Bloom level: {', '.join(levels)}.\n"
        "Return JSON array: [{\"bloom_level\":\"...\",\"question\":\"...\"}]\n"
        "Questions must reference the article content, not be generic."
    )


def build_flashcard_prompt(post: dict, articles: list[dict]) -> str:
    titles = "\n".join(f"- {a.get('title','?')}" for a in articles[:8])
    return (
        f"Post topic: \"{post['title']}\" ({post['pillar']})\n"
        f"Article titles:\n{titles}\n\n"
        "Extract up to 5 key concepts as flashcards in Polish.\n"
        "Return JSON array: [{\"term\":\"...\",\"definition\":\"...\"}]\n"
        "Terms should be specific (e.g. 'Beneficial Ownership Register' not 'Finance')."
    )


def extract_json(text: str) -> list | None:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0] if "```" in text else text
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                return None
    return None


def main():
    if not API_KEY:
        print("[-] LLM_API_KEY not set — skipping LLM enhancement")
        return 0

    articles_path = BASE_DIR / "static" / "api" / "articles.json"
    if not articles_path.exists():
        print("[-] articles.json not found — run generate_metadata.py first")
        return 1

    data = json.loads(articles_path.read_text(encoding="utf-8"))
    posts = data.get("posts", [])
    print(f"[*] LLM: {len(posts)} posts available, MAX_POSTS={MAX_POSTS}")

    llm_questions = []
    llm_flashcards = []
    processed = 0

    for post in posts[:MAX_POSTS]:
        articles = post.get("articles", [])
        if not articles:
            continue

        pid = f"{post['pillar']}/{post['date']}"
        print(f"  [{processed+1}] {pid} ...", end=" ", flush=True)

        # Quiz
        q_prompt = build_quiz_prompt(post, articles)
        q_system = (
            "You generate educational quiz questions following Bloom's Taxonomy. "
            "Return ONLY valid JSON, no markdown."
        )
        q_response = llm_complete(q_prompt, q_system)
        if q_response:
            qs = extract_json(q_response)
            if qs and isinstance(qs, list):
                for q in qs:
                    q["post_url"] = post.get("url", f"/daily/{pid}/")
                    q["pillar"] = post.get("pillar", "")
                    q["date"] = post.get("date", "")
                    q["source"] = "llm"
                    llm_questions.append(q)
                print(f"quiz:{len(qs)}", end=" ", flush=True)

        # Flashcards
        f_prompt = build_flashcard_prompt(post, articles)
        f_system = (
            "You extract educational flashcards. "
            "Return ONLY valid JSON array, no markdown."
        )
        f_response = llm_complete(f_prompt, f_system)
        if f_response:
            cs = extract_json(f_response)
            if cs and isinstance(cs, list):
                for c in cs:
                    c["source"] = post.get("url", f"/daily/{pid}/")
                    c["pillar"] = post.get("pillar", "")
                    c["date"] = post.get("date", "")
                    c["source_type"] = "llm"
                    llm_flashcards.append(c)
                print(f"fc:{len(cs)}", end=" ", flush=True)

        print()
        processed += 1

    print(f"\n[*] LLM generated: {len(llm_questions)} questions, {len(llm_flashcards)} flashcards")

    # Read current quiz.json and merge
    quiz_path = BASE_DIR / "static" / "api" / "quiz.json"
    if quiz_path.exists() and llm_questions:
        quiz = json.loads(quiz_path.read_text(encoding="utf-8"))
        existing = quiz.get("questions", [])
        # Remove existing LLM-generated entries (replacement)
        existing = [q for q in existing if q.get("source") != "llm"]
        existing.extend(llm_questions)
        quiz["questions"] = existing
        quiz["count"] = len(existing)
        quiz["llm_enhanced"] = datetime.now(timezone.utc).isoformat()
        quiz_path.write_text(
            json.dumps(quiz, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[+] Quiz enhanced: {quiz_path} ({len(existing)} total, {len(llm_questions)} LLM)")

    # Read current flashcards.json and merge
    fc_path = BASE_DIR / "static" / "api" / "flashcards.json"
    if fc_path.exists() and llm_flashcards:
        fc = json.loads(fc_path.read_text(encoding="utf-8"))
        existing_cards = fc.get("cards", [])
        existing_cards = [c for c in existing_cards if c.get("source_type") != "llm"]
        # Deduplicate by term
        seen_terms = {c["term"] for c in existing_cards}
        for c in llm_flashcards:
            if c["term"] not in seen_terms:
                seen_terms.add(c["term"])
                existing_cards.append(c)
        fc["cards"] = existing_cards
        fc["count"] = len(existing_cards)
        fc["llm_enhanced"] = datetime.now(timezone.utc).isoformat()
        fc_path.write_text(
            json.dumps(fc, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[+] Flashcards enhanced: {fc_path} ({len(existing_cards)} total, {len(llm_flashcards)} LLM)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
