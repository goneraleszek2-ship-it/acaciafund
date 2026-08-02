#!/usr/bin/env python3
"""Generate popular-science "explainer" knowledge pages for each pillar.

Creates warm, friendly, easy-to-understand explainers that communicate each
pillar's basic ideas through plain language, everyday analogies, and simple
inline SVG visuals. Designed for absolute beginners and general readers.

Usage:
    python3 scripts/generate_explainers.py          # add pages to registry
    python3 scripts/generate_explainers.py --dry-run # preview without writing
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"

NOW = datetime.now(timezone.utc).isoformat()
TODAY_STR = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_item(slug: str, title: str, description: str, pillar: str,
              body_html: str, tags: list[str]) -> dict:
    return {
        "slug": slug,
        "language": "en",
        "title": title,
        "description": description,
        "body_html": body_html,
        "content_type": "knowledge",
        "knowledge_category": "foundations",
        "category": "foundations",
        "pillar": pillar,
        "tags": tags,
        "difficulty": "beginner",
        "bloom_questions": [
            {"level": "remember", "question": "In one sentence, what is this concept really about?"},
            {"level": "understand", "question": "Explain the core idea to a friend using the analogy from this page."},
            {"level": "apply", "question": "Think of one small example of this idea happening in your own daily life."},
        ],
        "flashcards": [],
        "source_breakdown": {},
        "signals": {},
        "quality_metrics": {},
        "sqi": 0.8,
        "reading_time": max(1, len(body_html.split()) // 200),
        "deprecated": False,
        "created_at": NOW,
        "updated_at": NOW,
        "enriched": True,
        "enriched_at": NOW,
        "date_str": TODAY_STR,
    }


# ── SVG visual helpers ────────────────────────────────────────────────────
def svg_wrap(inner: str, height: int = 140) -> str:
    return (
        f'<div class="explainer-visual" role="img" aria-hidden="true">'
        f'<svg viewBox="0 0 560 {height}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;border-radius:12px;background:#f5f5f4">'
        f"{inner}</svg></div>"
    )


SVG_KYC = svg_wrap("""
<g stroke-width="2">
  <circle cx="120" cy="70" r="34" fill="#fcd9bd" stroke="#ea580c"/>
  <circle cx="120" cy="58" r="9" fill="#f5f5f4" stroke="#ea580c"/>
  <path d="M120 62 L120 88" stroke="#ea580c"/>
  <path d="M100 76 L120 88 L140 76" stroke="#ea580c"/>
  <rect x="300" y="42" width="180" height="60" rx="10" fill="#ffffff" stroke="#d6d3d1"/>
  <rect x="320" y="58" width="140" height="10" rx="5" fill="#d6d3d1"/>
  <rect x="320" y="74" width="90" height="8" rx="4" fill="#e7e5e4"/>
  <path d="M240 72 L300 72" stroke="#a8a29e" stroke-dasharray="6 6"/>
  <path d="M240 72 L210 72" stroke="#a8a29e" stroke-dasharray="6 6"/>
  <text x="150" y="150" font-size="14" fill="#78716c" text-anchor="middle" font-family="sans-serif">You</text>
  <text x="390" y="150" font-size="14" fill="#78716c" text-anchor="middle" font-family="sans-serif">Your record</text>
  <text x="200" y="28" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">simple, human trust</text>
  <text x="395" y="28" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">formal check</text>
</g>
""", 170)

SVG_SAR = svg_wrap("""
<g stroke-width="2">
  <circle cx="90" cy="70" r="8" fill="#fcd9bd" stroke="#ea580c"/>
  <circle cx="150" cy="40" r="8" fill="#fcd9bd" stroke="#ea580c"/>
  <circle cx="150" cy="100" r="8" fill="#fcd9bd" stroke="#ea580c"/>
  <circle cx="220" cy="70" r="8" fill="#fcd9bd" stroke="#ea580c"/>
  <path d="M98 66 L142 44 M98 74 L142 96 M158 46 L212 68 M158 94 L212 72" stroke="#a8a29e"/>
  <path d="M228 70 L250 70" stroke="#a8a29e" stroke-dasharray="5 5"/>
  <path d="M278 70 Q290 70 290 82 Q290 94 302 94 L320 94" fill="none" stroke="#ea580c"/>
  <path d="M320 88 L320 100 L332 94 Z" fill="#ea580c"/>
  <circle cx="360" cy="70" r="30" fill="#fff7ed" stroke="#ea580c"/>
  <path d="M360 52 L360 88 M344 62 L360 70 L376 62" stroke="#ea580c" fill="none"/>
  <text x="120" y="135" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">many small moments</text>
  <text x="360" y="125" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">one clear story</text>
</g>
""", 150)

SVG_LOB = svg_wrap("""
<g stroke-width="2">
  <line x1="60" y1="30" x2="60" y2="120" stroke="#d6d3d1"/>
  <line x1="500" y1="30" x2="500" y2="120" stroke="#d6d3d1"/>
  <line x1="60" y1="75" x2="500" y2="75" stroke="#d6d3d1" stroke-dasharray="6 6"/>
  <g fill="#dcfce7" stroke="#16a34a">
    <rect x="180" y="66" width="80" height="14" rx="7"/><rect x="180" y="48" width="80" height="14" rx="7"/><rect x="180" y="30" width="80" height="14" rx="7"/>
  </g>
  <g fill="#fee2e2" stroke="#dc2626">
    <rect x="300" y="82" width="80" height="14" rx="7"/><rect x="300" y="100" width="80" height="14" rx="7"/><rect x="300" y="118" width="80" height="14" rx="7"/>
  </g>
  <text x="220" y="20" font-size="12" fill="#16a34a" text-anchor="middle" font-family="sans-serif">BID (want to buy)</text>
  <text x="340" y="152" font-size="12" fill="#dc2626" text-anchor="middle" font-family="sans-serif">ASK (want to sell)</text>
  <text x="280" y="60" font-size="12" fill="#78716c" text-anchor="middle" font-family="sans-serif">price</text>
  <text x="510" y="80" font-size="12" fill="#a8a29e" text-anchor="middle" font-family="sans-serif"></text>
</g>
""", 165)

SVG_VOL = svg_wrap("""
<g stroke-width="2" fill="none" stroke-linecap="round">
  <path d="M40 90 Q60 90 80 70 T120 70 T160 40 T200 100 T240 50 T280 80 T320 60 T360 95 T400 60 T440 80 T480 70 T520 65" stroke="#16a34a"/>
  <path d="M40 90 Q70 88 100 90 T160 88 T220 90 T280 89 T340 90 T400 89 T460 90 T520 90" stroke="#a8a29e"/>
  <line x1="40" y1="90" x2="40" y2="30" stroke="#d6d3d1"/>
  <line x1="40" y1="90" x2="520" y2="90" stroke="#d6d3d1"/>
  <text x="250" y="25" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">heartbeat of the market</text>
  <text x="130" y="118" font-size="12" fill="#a8a29e" text-anchor="middle" font-family="sans-serif">gentle days</text>
  <text x="420" y="118" font-size="12" fill="#a8a29e" text-anchor="middle" font-family="sans-serif">loud days</text>
</g>
""", 130)

SVG_ETL = svg_wrap("""
<g stroke-width="2">
  <rect x="40" y="45" width="90" height="60" rx="12" fill="#fef3c7" stroke="#d97706"/>
  <rect x="70" y="58" width="30" height="18" rx="4" fill="#fbbf24"/><circle cx="80" cy="80" r="6" fill="#f59e0b"/>
  <rect x="70" y="82" width="40" height="8" rx="4" fill="#fcd34d"/>
  <path d="M150 75 L200 75" stroke="#a8a29e" stroke-dasharray="6 6"/>
  <rect x="215" y="45" width="110" height="60" rx="12" fill="#e0e7ff" stroke="#6366f1"/>
  <rect x="245" y="58" width="50" height="10" rx="5" fill="#818cf8"/><rect x="245" y="74" width="40" height="8" rx="4" fill="#a5b4fc"/>
  <path d="M345 75 L395 75" stroke="#a8a29e" stroke-dasharray="6 6"/>
  <rect x="410" y="45" width="110" height="60" rx="12" fill="#dcfce7" stroke="#16a34a"/>
  <rect x="440" y="58" width="50" height="10" rx="5" fill="#4ade80"/><rect x="440" y="74" width="56" height="8" rx="4" fill="#86efac"/>
  <text x="85" y="128" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">raw ingredients</text>
  <text x="270" y="128" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">wash + chop</text>
  <text x="465" y="128" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">serve the meal</text>
</g>
""", 145)

SVG_SCHEMA = svg_wrap("""
<g stroke-width="2">
  <rect x="40" y="50" width="110" height="60" rx="12" fill="#fff7ed" stroke="#ea580c"/>
  <text x="95" y="86" font-size="14" fill="#ea580c" text-anchor="middle" font-family="sans-serif">"book"</text>
  <rect x="410" y="50" width="110" height="60" rx="12" fill="#e0e7ff" stroke="#6366f1"/>
  <text x="465" y="86" font-size="14" fill="#6366f1" text-anchor="middle" font-family="sans-serif">"livre"</text>
  <rect x="205" y="58" width="150" height="44" rx="12" fill="#ffffff" stroke="#d6d3d1"/>
  <path d="M225 70 L230 80 M240 70 L240 80 M250 70 L245 80 M260 70 L258 80 M275 70 L272 80 M285 70 L282 80" stroke="#a8a29e"/>
  <text x="280" y="55" font-size="12" fill="#78716c" text-anchor="middle" font-family="sans-serif">shared dictionary</text>
  <path d="M150 80 L205 80 M355 80 L410 80" stroke="#78716c"/>
  <text x="280" y="132" font-size="13" fill="#78716c" text-anchor="middle" font-family="sans-serif">two systems, one meaning</text>
</g>
""", 145)


# ── Pillar 1: Compliance ──────────────────────────────────────────────────

KYC_BODY = f"""
{SVG_KYC}
<h2>The one-sentence version</h2>
<p>Know Your Customer (KYC) is the polite way a bank says: <em>"before I trust you with my money, let me get to know you a little."</em></p>

<h2>The everyday analogy</h2>
<p>Think of your favourite neighbourhood café. On day one, the barista just takes your order — cash, cup, done. But after a few visits you become <em>the person who takes their coffee with oat milk, extra hot</em>. The café knows you, and knowing you lets it serve you better — and notice if something ever seems off.</p>
<p>Banks can't get to know you at a counter, so they use documents and data instead: your ID, your address, who really owns your money. It's the same instinct — <em>build trust through understanding</em> — just scaled up to millions of customers.</p>

<h2>How it actually works</h2>
<ul>
<li><strong>Who are you?</strong> A real identity, backed by a government document.</li>
<li><strong>Who really benefits?</strong> Banks look past company names to the people behind them (beneficial ownership).</li>
<li><strong>How risky is your profile?</strong> Politicians, people in high-risk regions, and unusual ownership structures get a closer look.</li>
</ul>
<p>None of this is meant to be unfriendly. It's the financial world's way of keeping the neighbourhood safe so that everyone — including you — can keep doing business with confidence.</p>

<h2>Why this matters to you</h2>
<p>Every time a bank asks a few more questions, it's quietly protecting the whole community from fraud and crime. Understanding KYC means understanding the simple, human idea at its heart: <strong>trust is built on knowledge.</strong> And now you know the trick.</p>
"""

SAR_BODY = f"""
{SVG_SAR}
<h2>The one-sentence version</h2>
<p>A Suspicious Activity Report (SAR) is a bank saying to the authorities: <em>"I noticed something a little odd — not proof of anything, but worth a closer look."</em></p>

<h2>The everyday analogy</h2>
<p>A library has a rule: you may borrow three books at a time. A reader borrows exactly three every single day — always on the same topics, always returning them at 9am sharp, always in cash for late fees. None of this breaks a rule. But the librarian would be a poor guardian of the library if she never paused and thought, <em>hmm, that's interesting</em>.</p>
<p>That's all a SAR is: a librarian's thoughtful "hmm, interesting" — recorded and passed along. It is a <em>signal</em>, not a verdict. Innocent until proven otherwise, but too important to ignore.</p>

<h2>How it actually works</h2>
<ul>
<li><strong>Patterns, not moments:</strong> one large transfer is usually nothing; a careful <em>pattern</em> of small ones that dance around reporting limits is curious.</li>
<li><strong>No accusation:</strong> a SAR protects the bank and the system. It doesn't assume you've done anything wrong.</li>
<li><strong>Connecting the dots:</strong> authorities receive many quiet signals; together those signals can reveal a story no single bank could see.</li>
</ul>

<h2>Why this matters to you</h2>
<p>You now understand one of the most misunderstood things in finance. When a bank watches for odd patterns, it's acting like a good neighbour — <strong>paying attention so problems stay small.</strong> That attention is what makes everyday finance safe for everyone else.</p>
"""

# ── Pillar 2: Markets ─────────────────────────────────────────────────────

LOB_BODY = f"""
{SVG_LOB}
<h2>The one-sentence version</h2>
<p>An order book is a public queue where buyers shout the highest price they'll pay and sellers shout the lowest price they'll accept — and trades happen the moment two voices meet.</p>

<h2>The everyday analogy</h2>
<p>Imagine a farmers' market with a chalkboard in the middle. Buyers write "I'll pay 4 for a punnet of berries." Sellers write "I'll sell mine for 5." The board shows every offer, from best to worst, on each side.</p>
<p>When a buyer raises their bid to 5 — or a seller drops their ask to 4 — they match, the chalk is erased, and a trade is done. No drama, no middlemen: <em>just people publicly declaring their best offer and meeting in the middle.</em></p>

<h2>How it actually works</h2>
<ul>
<li><strong>Bids and asks:</strong> buyers line up by price (highest first), sellers too (lowest first).</li>
<li><strong>The spread:</strong> the gap between the best bid and best ask. A narrow gap means a liquid, easy-to-trade market.</li>
<li><strong>Price is a conversation:</strong> every price you see is the collective decision of everyone at the table, updated in real time.</li>
</ul>

<h2>Why this matters to you</h2>
<p>Order books explain the most important number in the world — the price of things — as a simple human conversation. Next time you see a price tick, imagine two people at a market quietly agreeing. <strong>Markets aren't magic; they're mathematics made by people.</strong> And now you can read the board.</p>
"""

VOL_BODY = f"""
{SVG_VOL}
<h2>The one-sentence version</h2>
<p>Volatility is the market's heart rate — a measure of how loudly and quickly prices are changing, not whether the direction is good or bad.</p>

<h2>The everyday analogy</h2>
<p>A lake on a calm morning is flat and glassy — beautiful, easy to row across. A river after rain is fast, bumpy, and loud. Both are just water; they differ in <em>how much they move</em>. Volatility is exactly that: the size of the ripples, not the direction of the current.</p>
<p>High volatility doesn't mean the market is "failing." It means prices are moving in bigger steps — like a white-water ride. For a careful paddler, that's exciting; for someone who hates surprises, it's a good day to sit on the bank and watch.</p>

<h2>How it actually works</h2>
<ul>
<li><strong>Measured by movement:</strong> how far and how fast prices swing around their average.</li>
<li><strong>Not direction:</strong> a market can be very volatile and still end up higher than it started.</li>
<li><strong>A tool, not a threat:</strong> knowing volatility is like checking the weather — it tells you how to pack for the trip.</li>
</ul>

<h2>Why this matters to you</h2>
<p>Volatility is the difference between being scared by a bumpy ride and being prepared for one. Understand it, and a scary chart becomes just weather you know how to read. <strong>Resilience is built by understanding — not by avoiding the storm.</strong></p>
"""

# ── Pillar 3: Data Engineering ────────────────────────────────────────────

ETL_BODY = f"""
{SVG_ETL}
<h2>The one-sentence version</h2>
<p>ETL (Extract, Transform, Load) is the kitchen of the data world: ingredients come in raw, get washed and chopped and cooked, and come out as a meal anyone can enjoy.</p>

<h2>The everyday analogy</h2>
<p>Follow a tomato's journey to your plate. Someone <em>extracts</em> it from the farm, a chef <em>transforms</em> it into sauce — peeling, seeding, simmering — and finally <em>loads</em> it onto a plate. You never see the farm, the dirt, or the chopping. You just get a delicious meal.</p>
<p>Data works the same way. A company's "farm" might be thousands of messy files, phone apps, and old spreadsheets. The ETL kitchen collects them, cleans and reshapes them into one consistent format, and serves them to analysts — who simply sit down and eat.</p>

<h2>How it actually works</h2>
<ul>
<li><strong>Extract:</strong> pull raw data from wherever it lives — databases, files, apps.</li>
<li><strong>Transform:</strong> clean it, fix inconsistencies, and shape it into a standard form.</li>
<li><strong>Load:</strong> place it somewhere useful, like a data warehouse, ready to query.</li>
</ul>

<h2>Why this matters to you</h2>
<p>Every recommendation, insight, and honest report you read started as a messy pile of ingredients. ETL is the quiet kitchen making sense of it all. Next time you trust a number, remember: <strong>someone washed the tomatoes.</strong> Clean data is what turns information into understanding.</p>
"""

SCHEMA_BODY = f"""
{SVG_SCHEMA}
<h2>The one-sentence version</h2>
<p>A schema is a shared dictionary that lets two computer systems exchange information without talking past each other.</p>

<h2>The everyday analogy</h2>
<p>You and a friend agree to meet at "the usual place." That phrase works perfectly — because the two of you share the same dictionary, and "the usual place" means one specific café to both of you.</p>
<p>But ask a stranger to meet you at "the usual place" and they'd be lost. Computer systems are strangers to one another. One system might call a thing "customer," another "client," another "buyer." A schema is the agreement: <em>"we'll all use 'customer,' and it always means a name plus an address plus an email."</em> Suddenly, every system speaks the same language.</p>

<h2>How it actually works</h2>
<ul>
<li><strong>Shape:</strong> which fields exist (name, date, amount) and what type each one is (text, number).</li>
<li><strong>Rules:</strong> what's required, what's optional, what values are allowed.</li>
<li><strong>Evolution:</strong> when the dictionary needs a new word, everyone agrees on the change first — so nothing breaks.</li>
</ul>

<h2>Why this matters to you</h2>
<p>Every time two apps work together seamlessly — your bank syncing your phone, your calendar meeting your email — a schema is doing the translating. <strong>Shared understanding is the quiet superpower behind a connected world.</strong> And a schema is just that, written down.</p>
"""


def main():
    dry_run = "--dry-run" in sys.argv

    registry = load_json(REGISTRY_PATH)
    existing_slugs = {item["slug"] for item in registry.get("content", [])}

    PAGES = [
        make_item(
            "compliance/knowledge/explainer-kyc",
            "Know Your Customer: Why banks ask for your ID",
            "A friendly, plain-English tour of KYC — the simple human idea of building trust through knowledge, told with the everyday analogy of a neighbourhood café.",
            "aml",
            KYC_BODY,
            ["explainer", "eli5", "kyc", "compliance", "beginner", "trust"],
        ),
        make_item(
            "compliance/knowledge/explainer-sar",
            "Suspicious Activity: When many small moments tell one story",
            "What a Suspicious Activity Report really is — a librarian's thoughtful 'hmm, interesting,' not an accusation. Understand the pattern-spotting heart of AML.",
            "aml",
            SAR_BODY,
            ["explainer", "eli5", "sar", "transaction-monitoring", "aml", "beginner"],
        ),
        make_item(
            "markets/knowledge/explainer-order-book",
            "The Order Book: A market where everyone shouts their price",
            "How buy and sell orders meet like haggling at a farmers' market — and why the price of anything is just a public conversation in real time.",
            "stock",
            LOB_BODY,
            ["explainer", "eli5", "order-book", "market-microstructure", "markets", "beginner"],
        ),
        make_item(
            "markets/knowledge/explainer-volatility",
            "Volatility: The market's heart rate",
            "Why a bumpy market is like white-water rafting — volatility is about the size of the ripples, not the direction of the current. Learn to read the weather.",
            "stock",
            VOL_BODY,
            ["explainer", "eli5", "volatility", "markets", "risk", "beginner"],
        ),
        make_item(
            "data/knowledge/explainer-etl",
            "ETL: The kitchen where raw data becomes a meal",
            "Extract, Transform, Load explained as a tomato's journey from farm to plate — and why every trustworthy number got its vegetables washed first.",
            "data-engineering",
            ETL_BODY,
            ["explainer", "eli5", "etl", "data-engineering", "pipeline", "beginner"],
        ),
        make_item(
            "data/knowledge/explainer-schema",
            "Schema: The dictionary that lets two systems agree",
            "Why computers need a shared language to cooperate — and how 'the usual place' becomes a written agreement between strangers.",
            "data-engineering",
            SCHEMA_BODY,
            ["explainer", "eli5", "schema", "data-contracts", "data-engineering", "beginner"],
        ),
    ]

    added = 0
    skipped = 0
    for page in PAGES:
        if page["slug"] in existing_slugs:
            skipped += 1
            if dry_run:
                print(f"  [SKIP] {page['slug']} — already exists")
            continue
        registry["content"].append(page)
        added += 1
        if dry_run:
            print(f"  [ADD]  {page['slug']} — would be added")
        else:
            print(f"  [ADD]  {page['slug']}")

    if not dry_run and added > 0:
        for item in registry["content"]:
            if item.get("body_html"):
                item["reading_time"] = max(1, len(item["body_html"].split()) // 200)
        save_json(REGISTRY_PATH, registry)
        print(f"\nAdded {added} explainer pages ({skipped} skipped)")
        print(f"Registry now has {len(registry['content'])} content items")
    elif dry_run:
        print(f"\nDry run: {added} would be added, {skipped} skipped (already exist)")
    else:
        print(f"Nothing to add ({skipped} already exist)")


if __name__ == "__main__":
    main()
