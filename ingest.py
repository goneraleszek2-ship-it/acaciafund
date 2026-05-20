#!/usr/bin/env python3
"""AcaciaFund — daily automated research synthesis pipeline.

Scrapes HackerNews (Algolia API) top stories, classifies them into 3 pillars
(AML, Markets, Science), and generates dated Hugo markdown posts with
contextual analysis.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "daily"

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
USER_AGENT = "AcaciaFund/2.0"
HN_DISCUSSION_URL = "https://news.ycombinator.com/item?id={}"

# ── pillar definitions with rich keywords & domain heuristics ────────────────
PILLARS = {
    "aml": {
        "label": "AML",
        "emoji": "🛡️",
        "folder": CONTENT_DIR / "aml",
        "tags": ["aml", "compliance", "regtech", "financial-crime"],
        "description": "Ewolucja systemów odpornościowych w sektorze finansowym",
        "keywords": [
            "aml", "anti-money laundering", "compliance", "regtech",
            "financial crime", "sanctions", "money laundering",
            "know your customer", "kyc", "counter-terrorism financing",
            "ctf", "financial action task force", "fatf", "beneficial ownership",
            "shell company", "offshore", "fraud detection", "transaction monitoring",
            "sar", "suspicious activity", "banking regulation", "basel",
            "fintech", "psd2", "gdpr", "data privacy", "data breach",
            "cybersecurity", "cyber security", "ransomware", "phishing",
            "payment", "payment system", "central bank digital currency",
            "cbdc", "sovereign payment", "digital euro", "open banking",
            "financial inclusion", "anti-fraud", "identity theft",
            "credit card fraud", "bank fraud", "insider trading",
            "market manipulation", "securities fraud", "crypto regulation",
            "cryptocurrency regulation", "digital asset regulation",
            "sec", "financial conduct", "consumer financial protection",
            "bank secrecy", "patriot act", "trade surveillance",
        ],
        "domain_scores": {
            "fincen.gov": 10, "fatf-gafi.org": 10, "fca.org.uk": 8,
            "occ.gov": 8, "bis.org": 7, "ec.europa.eu": 6,
            "cointelegraph.com": 4, "coindesk.com": 4,
        },
    },
    "stock": {
        "label": "STOCK",
        "emoji": "📈",
        "folder": CONTENT_DIR / "stock",
        "tags": ["markets", "stocks", "semiconductors", "hardware"],
        "description": "Analiza rynków kapitałowych i półprzewodników",
        "keywords": [
            "semiconductor", "nvidia", "tsmc", "asml", "intel", "amd",
            "chip", "chips", "microchip", "foundry", "fab",
            "valuation", "earnings", "stock market", "nasdaq", "s&p 500",
            "supply chain", "hardware", "processor", "gpu", "asic",
            "arm", "risc-v", "apple silicon", "quantum computing",
            "venture capital", "startup funding", "ipo", "spac",
            "institutional investor", "hedge fund", "activist investor",
        ],
        "domain_scores": {
            "nvidia.com": 10, "tsmc.com": 10, "asml.com": 10,
            "intel.com": 8, "amd.com": 8, "semiengineering.com": 9,
            "anandtech.com": 7, "tomshardware.com": 7,
            "bloomberg.com": 5, "reuters.com": 5, "wsj.com": 5,
            "ft.com": 5, "seekingalpha.com": 6,
        },
    },
    "science": {
        "label": "SCIENCE",
        "emoji": "🧬",
        "folder": CONTENT_DIR / "science",
        "tags": ["science", "systems", "cybernetics", "complexity"],
        "description": "Nauka, systemy złożone i ewolucja poznawcza",
        "keywords": [
            "cybernetics", "mitochondria", "bioenergetics", "systems theory",
            "complexity", "emergence", "self-organization", "autopoiesis",
            "antifragile", "antifragility", "black swan", "taleb",
            "cognitive science", "neuroscience", "consciousness",
            "artificial life", "origin of life", "evolutionary biology",
            "epigenetics", "crispr", "gene therapy", "longevity",
            "mitochondrial", "cellular metabolism", "biohacking",
            "network theory", "graph theory", "scale-free",
        ],
        "domain_scores": {
            "nature.com": 10, "science.org": 10, "cell.com": 9,
            "pnas.org": 9, "biorxiv.org": 8, "arxiv.org": 7,
            "sciencedirect.com": 7, "scientificamerican.com": 8,
            "quantamagazine.org": 9, "nautil.us": 7, "aeon.co": 6,
        },
    },
}

STOP_WORDS = {
    "the", "a", "an", "of", "in", "to", "for", "and", "is", "on",
    "that", "with", "from", "by", "at", "its", "it", "as", "are",
    "be", "has", "have", "was", "were", "new", "how", "why", "what",
    "show", "ask", "tell", "this", "we", "our", "their", "they",
    "not", "no", "but", "all", "about", "up", "out", "over",
    "after", "into", "than", "then", "also", "just", "more",
}

DOMAIN_TAXONOMY = {
    "nauka": {"nature.com", "science.org", "cell.com", "pnas.org", "biorxiv.org", "arxiv.org", "quantamagazine.org", "sciencedirect.com", "scientificamerican.com"},
    "finanse": {"bloomberg.com", "reuters.com", "wsj.com", "ft.com", "seekingalpha.com", "marketwatch.com", "investopedia.com"},
    "regulacje": {"fincen.gov", "fatf-gafi.org", "fca.org.uk", "sec.gov", "occ.gov", "bis.org", "ec.europa.eu"},
    "technologia": {"arstechnica.com", "techcrunch.com", "theverge.com", "wired.com", "anandtech.com", "tomshardware.com", "semiengineering.com"},
    "media": {"nytimes.com", "theguardian.com", "bbc.com", "apnews.com", "gizmodo.com", "cnn.com", "npr.org"},
}

KNOWN_ENTITIES = {
    "aml": {"FinCEN", "FATF", "SEC", "FCA", "ECB", "Fed", "OCC", "EBA", "Binance", "Coinbase", "Circle", "PayPal", "Stripe", "Block", "JPMorgan", "Goldman Sachs", "HSBC", "Deutsche Bank", "Citi", "Visa", "Mastercard", "SWIFT", "Pix", "FedNow"},
    "stock": {"NVIDIA", "AMD", "TSMC", "Intel", "ASML", "Apple", "Microsoft", "Samsung", "Qualcomm", "ARM", "Broadcom", "Micron", "Amazon", "Google", "Meta", "Tesla", "OpenAI", "SoftBank"},
    "science": {"OpenAI", "DeepMind", "Google AI", "Meta AI", "Anthropic", "xAI", "MIT", "Stanford", "Harvard", "Oxford", "Cambridge", "Caltech", "DARPA", "NIH", "CERN", "NASA", "ESA", "WHO"},
}
ALL_ENTITIES = set().union(*KNOWN_ENTITIES.values())

def categorize_domain(domain: str) -> str:
    for cat, domains in DOMAIN_TAXONOMY.items():
        if any(d in domain for d in domains):
            return cat
    return "inne"

def extract_entities(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for ent in sorted(ALL_ENTITIES, key=len, reverse=True):
        if ent.lower() in text_lower:
            found.append(ent)
    return found[:5]

def build_pillar_signals(stories: list[dict], pillar_name: str) -> dict:
    if not stories:
        return {}
    scores = [s["points"] for s in stories]
    avg = sum(scores) / len(scores)
    max_s = max(scores)
    domains = [categorize_domain(extract_domain(s.get("url", ""))) for s in stories]
    domain_counts = Counter(domains)
    all_entities = []
    for s in stories:
        all_entities.extend(extract_entities(s["title"]))
    entity_counts = Counter(all_entities)
    return {
        "count": len(stories),
        "avg_score": avg,
        "max_score": max_s,
        "total_score": sum(scores),
        "has_outlier": max_s > 3 * avg if avg > 0 else False,
        "outlier_ratio": max_s / (avg or 1),
        "score_skew": "outlier" if max_s > 3 * avg and avg > 0 else "balanced",
        "domain_diversity": len(domain_counts),
        "top_domain": domain_counts.most_common(1)[0][0] if domain_counts else "nieznane",
        "top_domain_share": domain_counts.most_common(1)[0][1] / len(stories) if stories else 0,
        "top_entities": [e for e, _ in entity_counts.most_common(5)],
        "entity_coherence": "high" if entity_counts and len(entity_counts) < max(2, len(stories) * 0.4) else "low",
    }

RULES_META = [
    {"name": "outlier_dominance", "match": lambda s: s.get("has_outlier") and s.get("score_skew") == "outlier", "generate": lambda s, stories, pname: (f"Uwagę społeczności zdominował jeden sygnał: „**{stories[0]['title']}**” ({stories[0]['points']}⭐) — to {s['outlier_ratio']:.1f}x więcej niż średnia pozostałych. Dominująca kategoria źródła: **{s['top_domain']}**. Z perspektywy systemowej to klasyczny efekt kaskady informacyjnej: wysoka gęstość sprzężenia zwrotnego wokół jednego bodźca wywołuje nieliniową amplifikację sygnału.")},
    {"name": "high_diversity", "match": lambda s: s.get("domain_diversity", 0) >= 4 and s.get("count", 0) >= 10, "generate": lambda s, stories, pname: (f"Zarejestrowano {s['count']} sygnałów z **{s['domain_diversity']} różnych kategorii źródeł** ({', '.join(k for k, v in Counter([categorize_domain(extract_domain(x.get('url',''))) for x in stories]).most_common(3))}), co wskazuje na wysoką entropię informacyjną. Topowe encje: {', '.join(s['top_entities'][:4]) or 'brak rozpoznawalnych'}. Taka dyfuzja źródeł sugeruje, że zjawisko ma charakter systemowy, a nie lokalny — rezonuje w różnych warstwach ekosystemu.")},
    {"name": "entity_cluster", "match": lambda s: s.get("entity_coherence") == "high" and s.get("count", 0) >= 5, "generate": lambda s, stories, pname: (f"Wysoka spójność encji ({', '.join(s['top_entities'][:3])}) przy {s['count']} artykułach świadczy o krystalizacji narracji wokół konkretnych podmiotów. System osiąga punkt krytyczny, w którym lokalne fluktuacje synchronizują się w emergentny wzorzec. To faza przejściowa — kolejne okno pokaże, czy trend się ustabilizuje.")},
    {"name": "low_volume", "match": lambda s: s.get("count", 0) <= 3 and s.get("count", 0) > 0, "generate": lambda s, stories, pname: (f"Niska gęstość sygnałów ({s['count']} artykułów) przy {'wysokiej' if s['max_score'] > 100 else 'niskiej'} punktacji (max {s['max_score']}⭐) sugeruje niszowy, ale {'potencjalnie znaczący' if s['max_score'] > 100 else 'wyspecjalizowany'} obszar dyskusji. W teorii systemów to okres ciszy przed ewentualną kaskadą — mała liczba agentów, wysoka energia sygnału.")},
    {"name": "balanced_activity", "match": lambda s: s.get("score_skew") == "balanced" and s.get("count", 0) > 3, "generate": lambda s, stories, pname: (f"Zrównoważony rozkład punktacji ({s['count']} artykułów, średnia {s['avg_score']:.0f}⭐, max {s['max_score']}⭐) wskazuje na dojrzałą dyskusję bez dominującego sygnału. Topowe encje: {', '.join(s['top_entities'][:3]) or 'różnorodne'}. Źródła z domeny **{s['top_domain']}** stanowią {s['top_domain_share']*100:.0f}% wszystkich. To ekosystem o wysokiej różnorodności — stabilny, ale podatny na zakłócenia zewnętrzne.")},
    {"name": "generic_high", "match": lambda s: s.get("count", 0) > 0, "generate": lambda s, stories, pname: (f"W obszarze {PILLARS[pname]['description'].lower()} odnotowano {s['count']} artykułów (łączna pula {s['total_score']}⭐, średnia {s['avg_score']:.0f}⭐). Najwyżej oceniony: „**{stories[0]['title']}**” ({stories[0]['points']}⭐). Dominująca kategoria źródła: **{s['top_domain']}**. Tematy wiodące: {', '.join(s['top_entities'][:3]) or 'różnorodne'}.")},
]

RULES_SYSTEMS = [
    {"name": "outlier_cascade", "match": lambda s: s.get("has_outlier") and s.get("max_score", 0) > 300, "generate": lambda s, stories, pname: (f"Mechanizm kaskady informacyjnej: sygnał outlierowy ({stories[0]['points']}⭐) uruchomił pętlę dodatniego sprzężenia zwrotnego — im więcej osób interagowało z treścią, tym wyżej algorytm HN ją wyniósł, generując dalszą ekspozycję. Z perspektywy cybernetycznej to przykład eskalacji bez homeostazy: system nie miał wbudowanego tłumika, który zrównoważyłby tę pętlę w czasie rzeczywistym. Konsekwencje: {', '.join(s['top_entities'][:2]) or 'temat'} może podlegać przeszacowaniu w kolejnych cyklach.")},
    {"name": "entropy_diversity", "match": lambda s: s.get("domain_diversity", 0) >= 4, "generate": lambda s, stories, pname: (f"Wysoka różnorodność źródeł ({s['domain_diversity']} kategorii) świadczy o rozproszonej generacji informacji — system nie ma centralnego agregatora, a emergentne wzorce powstają z lokalnych interakcji na peryferiach sieci. Zgodnie z drugą zasadą termodynamiki, wzrost entropii informacyjnej zmniejsza zdolność systemu do predykcji — ale zwiększa jego antykruchość poprzez redundancję ścieżek sygnałowych.")},
    {"name": "coherence_phase", "match": lambda s: s.get("entity_coherence") == "high", "generate": lambda s, stories, pname: (f"Krystalizacja narracji wokół {', '.join(s['top_entities'][:3])} to klasyczny obraz przejścia fazowego w systemie złożonym: lokalne fluktuacje (pojedyncze artykuły) osiągają masę krytyczną, po czym następuje synchronizacja faz. W tym momencie system znajduje się w stanie krytycznym — drobny impuls może przechylić równowagę w kierunku nowego attractora.")},
    {"name": "low_signal", "match": lambda s: s.get("count", 0) <= 3 and s.get("count", 0) > 0, "generate": lambda s, stories, pname: (f"Niska gęstość sygnałów przy jednoczesnej obecności tematów ({', '.join(s['top_entities'][:3]) or 'różnorodne'}) sugeruje stan przed-krytyczny: system kumuluje energię potencjalną, która może zostać uwolniona w kolejnym oknie obserwacji. W cybernetyce nazywamy to histerezą — opóźnioną odpowiedzią na bodziec poniżej progu aktywacji.")},
    {"name": "balanced_stable", "match": lambda s: s.get("score_skew") == "balanced" and s.get("count", 4) >= 4, "generate": lambda s, stories, pname: (f"Zrównoważony przepływ informacji ({s['count']} artykułów, skew ratio {s['outlier_ratio']:.1f}) wskazuje na stan homeostazy systemu. Pętle ujemnego sprzężenia zwrotnego skutecznie tłumią odchylenia, utrzymując system w basenie attractora. Z punktu widzenia antykruchości jest to oznaka zdrowej redundancji — wiele słabych sygnałów zamiast jednego dominującego.")},
    {"name": "generic_systems", "match": lambda s: s.get("count", 0) > 0, "generate": lambda s, stories, pname: (f"Analiza {s['count']} sygnałów w filarze {pname.upper()} ujawnia strukturę sieci o gęstości {'wysokiej' if s['count'] > 15 else 'średniej' if s['count'] > 5 else 'niskiej'}. Najsilniejszy węzeł: „{stories[0]['title']}” ({stories[0]['points']}⭐) z domeny {categorize_domain(extract_domain(stories[0].get('url','')))}. Rozkład przypomina sieć bezskalową — kilka węzłów skupia większość połączeń, reszta tworzy długi ogon dystrybucji.")},
]

RULES_CONN = [
    {"name": "shared_entities", "match": lambda cp: cp is not None and len(cp.get("shared_entities", [])) > 0, "generate": lambda cp, stories, pname: (f"Encja **{cp['shared_entities'][0]}** pojawiła się dziś zarówno w filarze **{cp['pair'][0].upper()}** jak i **{cp['pair'][1].upper()}** — realne cross-pillar połączenie. W filarze {pname.upper()} dotyczy to artykułu „{cp['article_a'][:80]}”. Z punktu widzenia teorii systemów, obecność tej samej encji w dwóch niezależnych domenach świadczy o istnieniu ukrytego połączenia strukturalnego — być może wspólnego źródła zakłóceń lub globalnego trendu, który manifestuje się lokalnie w różnych subsystemach.")},
    {"name": "pillar_synergy", "match": lambda cp: cp is not None and cp.get("strength", 0) > 0, "generate": lambda cp, stories, pname: (f"Przekrój tematyczny łączy filary {cp['pair'][0].upper()} i {cp['pair'][1].upper()} poprzez wspólne wątki ({' — '.join(cp['shared_entities'][:2])}). Z perspektywy multi-domenowej AcaciaFund, te same sygnały przetwarzane są przez różne warstwy abstrakcji — regulacyjną (AML), kapitałową (Markets) i poznawczą (Science). Rezonans między nimi amplifikuje znaczenie sygnału.")},
    {"name": "no_connection", "match": lambda cp: True, "generate": lambda cp, stories, pname: (f"W tym oknie czasowym nie wykryto silnych korelacji między filarami na poziomie encji. Z perspektywy multi-domenowej AcaciaFund, niezależność domen jest równie wartościowa — oznacza, że systemy peryferyjne nie są nadmiernie sprzężone, co zwiększa ogólną antykruchość portfela informacyjnego.")},
]

def apply_rules(rules: list[dict], signals: dict, stories: list[dict], pname: str, extra: any = None) -> str:
    for rule in rules:
        if rule["match"](signals if extra is None else extra):
            return rule["generate"](signals if extra is None else extra, stories, pname)
    return ""


# ── helpers ──────────────────────────────────────────────────────────────────

def log(msg: str, ok: bool = True) -> None:
    prefix = "[+]" if ok else "[-]"
    print(f"{prefix} {msg}", file=sys.stderr)


def extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else ""


def classify_story(story: dict) -> list[tuple[str, int]]:
    """Classify a story into pillars with confidence scores."""
    title = story.get("title", "").lower()
    url = story.get("url", "")
    domain = extract_domain(url)
    scores: list[tuple[str, int]] = []

    for pillar_name, config in PILLARS.items():
        score = 0

        # domain match (highest weight)
        for dom_pattern, dom_score in config["domain_scores"].items():
            if dom_pattern in domain:
                score += dom_score

        # keyword match in title (case-insensitive, word-boundary)
        for kw in config["keywords"]:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, title):
                score += 3

        if score > 0:
            scores.append((pillar_name, score))

    return scores


def fetch_top_stories(since_hours: int = 48, min_points: int = 2) -> list[dict]:
    """Fetch top stories from HN Algolia, optionally filtered by points.

    Uses a broad query + tag filter to get the best content from the window.
    """
    since_ts = int((datetime.now(timezone.utc) - timedelta(hours=since_hours)).timestamp())
    params = {
        "query": "",
        "tags": "story",
        "hitsPerPage": 1000,
        "numericFilters": f"created_at_i>{since_ts}",
    }
    url = f"{ALGOLIA_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        log(f"Błąd pobierania HN feed: {e}", ok=False)
        return []

    stories = []
    for hit in data.get("hits", []):
        title = (hit.get("title") or "").strip()
        if not title:
            continue

        points = hit.get("points", 0) or 0
        if points < min_points:
            continue

        object_id = hit.get("objectID", "")
        hn_url = HN_DISCUSSION_URL.format(object_id) if object_id else ""
        raw_url = hit.get("url") or hn_url

        stories.append({
            "title": title,
            "url": raw_url,
            "hn_url": hn_url,
            "points": points,
            "created_at": hit.get("created_at", ""),
            "author": hit.get("author", ""),
            "object_id": object_id,
        })

    stories.sort(key=lambda s: s["points"], reverse=True)
    return stories


def extract_themes(titles: list[str]) -> list[str]:
    """Extract recurring thematic keywords from story titles."""
    words = []
    for t in titles:
        cleaned = re.sub(r"[^a-z\s]", " ", t.lower())
        words.extend(w for w in cleaned.split() if len(w) > 3 and w not in STOP_WORDS)
    counts = Counter(words)
    return [w.capitalize() for w, _ in counts.most_common(5)]


def build_analysis(stories: list[dict], pillar_name: str,
                   all_pillar_stories: dict[str, list[dict]] | None = None) -> dict[str, str]:
    if not stories:
        return {
            "trending": f"*Brak nowych doniesień z ostatnich 48h dla tego obszaru.*\n\n*Pipeline AcaciaFund skanuje HN codziennie o 08:00 UTC.*",
            "metaanalysis": "Brak danych do analizy w tym oknie czasowym. To normalne dla wyspecjalizowanych obszarów badawczych — sygnały pojawiają się falami, nie codziennie.",
            "systems_lens": "Brak nowych sygnałów w tym oknie. Z punktu widzenia teorii systemów, brak informacji to również informacja — horyzont zdarzeń nie wygenerował wystarczającej gęstości sprzężenia zwrotnego do detekcji trendu.",
            "connections": "Brak korelacji w tym oknie czasowym. Analiza pozostaje otwarta na kolejny cykl skanowania.",
        }

    trending_lines = []
    for i, s in enumerate(stories[:7]):
        link_text = s["title"]
        extra = ""
        if s["hn_url"] and s["hn_url"] != s["url"]:
            extra = f" ([dyskusja]({s['hn_url']}))"
        trending_lines.append(f"{i+1}. [{link_text}]({s['url']}){extra} (⭐{s['points']})")
    trending = "\n".join(trending_lines)

    signals = build_pillar_signals(stories, pillar_name)

    meta = apply_rules(RULES_META, signals, stories, pillar_name)
    if not meta:
        meta = apply_rules([RULES_META[-1]], signals, stories, pillar_name)

    systems = apply_rules(RULES_SYSTEMS, signals, stories, pillar_name)
    if not systems:
        systems = apply_rules([RULES_SYSTEMS[-1]], signals, stories, pillar_name)

    cp_signal = None
    if all_pillar_stories:
        for p in all_pillar_stories:
            if p == pillar_name:
                continue
            p_stories = all_pillar_stories.get(p, [])
            if not p_stories:
                continue
            p_signals = build_pillar_signals(p_stories, p)
            shared = set(signals.get("top_entities", [])) & set(p_signals.get("top_entities", []))
            if shared:
                a_in_p = next((s["title"] for s in all_pillar_stories[pillar_name]
                              if any(e.lower() in s["title"].lower() for e in shared)), "")
                cp_signal = {"pair": (pillar_name, p), "shared_entities": list(shared), "strength": len(shared), "article_a": a_in_p}
                break

    conn = apply_rules(RULES_CONN, signals, stories, pillar_name, cp_signal)
    if not conn:
        conn = apply_rules([RULES_CONN[-1]], signals, stories, pillar_name, cp_signal)

    return {"trending": trending, "metaanalysis": meta, "systems_lens": systems, "connections": conn,}


def generate_post(pillar_name: str, config: dict, pillar_stories: list[dict],
                  all_pillar_stories: dict[str, list[dict]] | None = None) -> Path | None:
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    filename = f"{date_str}.md"
    filepath = config["folder"] / filename

    if filepath.exists():
        log(f"Post już istnieje: {filename} dla {pillar_name} — pomijam")
        return None

    analysis = build_analysis(pillar_stories, pillar_name, all_pillar_stories)

    total_score = sum(s["points"] for s in pillar_stories)
    avg_score = round(total_score / len(pillar_stories), 1) if pillar_stories else 0
    max_score = max((s["points"] for s in pillar_stories), default=0)
    link_count = len(pillar_stories)

    lines = [
        "---",
        f'title: "Synteza {config["emoji"]} {config["label"]} — {date_str}"',
        f"date: {date_str}",
        f'tags: {json.dumps(config["tags"])}',
        f'theme: "AcaciaFund — {config["description"]}"',
        "---",
        "",
        '<div class="metrics">',
        f'<div class="metric gold"><div class="value">{total_score}</div><div class="label">⭐ Suma</div></div>',
        f'<div class="metric"><div class="value">{avg_score}</div><div class="label">📊 Średnia</div></div>',
        f'<div class="metric"><div class="value">{max_score}</div><div class="label">🏆 Max</div></div>',
        f'<div class="metric"><div class="value">{link_count}</div><div class="label">🔗 Linki</div></div>',
        "</div>",
        "",
        f"## 🔍 Trending (HackerNews, ostatnie 48h)",
        "",
        analysis["trending"],
        "",
        '<div class="insight" style="border-left-color:var(--gold)">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--gold);margin:0 0 8px">⚡ Kluczowe</h3>',
        f"<p>{max_score} ⭐ to najwyższa ocena w tym oknie. Średnia: {avg_score} ⭐. Łącznie {total_score} ⭐ z {link_count} linków.</p>",
        "</div>",
        "",
        "",
        '<div class="insight" style="border-left-color:#3B6999">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#3B6999;margin:0 0 8px">📊 Metaanaliza</h3>',
        analysis["metaanalysis"],
        "</div>",
        "",
        '<div class="insight">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--gold);margin:0 0 8px">🧠 Systems Thinking</h3>',
        analysis["systems_lens"],
        "</div>",
        "",
        '<div class="insight" style="border-left-color:var(--navy-mid)">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--navy-mid);margin:0 0 8px">🔗 Cross-Pillar Atlas</h3>',
        analysis["connections"],
        "</div>",
        "",
        "---",
        f"*Raport wygenerowano {date_str} o {today.strftime('%H:%M')} UTC. "
        f"Źródło: Algolia HN API. Klasyfikacja: AcaciaFund NLP.*",
    ]

    config["folder"].mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    link_count = len(pillar_stories)
    log(f"Wygenerowano: {filepath.relative_to(BASE_DIR)} ({link_count} linków)")
    return filepath


# ── arXiv ingestion ──────────────────────────────────────────────────────────

ARXIV_CATEGORIES = {
    "aml": ["q-fin.GN", "q-fin.RM", "cs.CY", "cs.CR"],
    "stock": ["q-fin.ST", "q-fin.PM", "cs.AR", "cs.ET"],
    "science": ["q-bio.MN", "cs.NE", "cs.CC", "nlin.AO", "nlin.CG"],
}

ARXIV_KEYWORDS = {
    "aml": ["money laundering", "compliance", "financial regulation", "fraud detection",
            "blockchain", "cryptocurrency", "financial crime", "risk management"],
    "stock": ["semiconductor", "supply chain", "market microstructure", "asset pricing",
              "volatility", "portfolio", "valuation", "chip"],
    "science": ["mitochondria", "cybernetics", "complex systems", "network theory",
                "emergence", "self-organization", "bioenergetics", "cognitive"],
}


def fetch_arxiv(since_hours: int = 72, max_results: int = 100) -> list[dict]:
    """Fetch recent papers from arXiv API and classify into pillars."""
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    date_from = since.strftime("%Y%m%d%H%M%S")

    all_cats = [c for cats in ARXIV_CATEGORIES.values() for c in cats]
    query_str = "cat:" + "+OR+cat:".join(urllib.parse.quote(c, safe="") for c in all_cats)
    url = f"http://export.arxiv.org/api/query?search_query={query_str}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            xml = resp.read().decode("utf-8")
    except Exception as e:
        log(f"Błąd arXiv API: {e}", ok=False)
        return []

    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
    papers = []
    for entry in entries:
        title = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        abstract = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        link = re.search(r"<id>(.*?)</id>", entry)
        published = re.search(r"<published>(.*?)</published>", entry)
        cats = re.findall(r'term="(.*?)"', entry)

        if not (title and link):
            continue

        title_text = title.group(1).strip()
        abstract_text = abstract.group(1).strip() if abstract else ""
        full_text = (title_text + " " + abstract_text[:500]).lower()

        # classify into pillars
        paper_scores: list[tuple[str, int]] = []
        for pillar, kws in ARXIV_KEYWORDS.items():
            score = sum(3 for kw in kws if kw in full_text)
            for cat in cats:
                if cat in ARXIV_CATEGORIES.get(pillar, []):
                    score += 5
            if score > 0:
                paper_scores.append((pillar, score))

        if not paper_scores:
            continue

        best = max(paper_scores, key=lambda x: x[1])
        papers.append({
            "title": re.sub(r"\s+", " ", title_text),
            "url": link.group(1).strip().rstrip("/"),
            "abstract": re.sub(r"\s+", " ", abstract_text)[:200],
            "pillar": best[0],
            "score": best[1],
            "published": published.group(1).strip() if published else "",
            "categories": cats,
        })

    papers.sort(key=lambda p: p["score"], reverse=True)
    return papers


def inject_arxiv(pillar_stories: dict[str, list[dict]]) -> None:
    """Fetch arXiv papers and append them to pillar stories."""
    log("Pobieranie z arXiv API...")
    papers = fetch_arxiv(since_hours=72)
    log(f"Pobrano {len(papers)} pasujących prac z arXiv")

    for paper in papers:
        p = paper["pillar"]
        pillar_stories[p].append({
            "title": paper["title"],
            "url": paper["url"],
            "hn_url": "",
            "points": 0,
            "created_at": paper["published"],
            "author": "arXiv",
            "object_id": "",
        })
        log(f"  → {p}: {paper['title'][:70]}")


# ── entry ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55, file=sys.stderr)
    log(f"AcaciaFund — start potoku: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 55, file=sys.stderr)

    # 1. fetch top stories from HN
    log("Pobieranie top stories z HN (ostatnie 48h)...")
    all_stories = fetch_top_stories(since_hours=48, min_points=2)
    log(f"Pobrano {len(all_stories)} stories z HN")

    if not all_stories:
        log("Brak danych z HN — kończę", ok=False)
        return 1

    # 2. classify each story into pillars
    pillar_stories: dict[str, list[dict]] = {p: [] for p in PILLARS}
    unclassified = 0

    for story in all_stories:
        classifications = classify_story(story)
        if not classifications:
            unclassified += 1
            continue
        # assign to highest-scoring pillar
        best_pillar = max(classifications, key=lambda x: x[1])
        pillar_stories[best_pillar[0]].append(story)

    log(f"Skategoryzowano: AML={len(pillar_stories['aml'])}, "
        f"STOCK={len(pillar_stories['stock'])}, "
        f"SCIENCE={len(pillar_stories['science'])}, "
        f"nieskategoryzowane={unclassified}")

    # 2b. inject arXiv papers
    inject_arxiv(pillar_stories)

    # 3. sort each pillar by points, reserve 5 slots for arXiv (0-point)
    for p in pillar_stories:
        hn = [s for s in pillar_stories[p] if s.get("points", 0) > 0]
        arx = [s for s in pillar_stories[p] if s.get("points", 0) == 0]
        hn.sort(key=lambda s: s["points"], reverse=True)
        pillar_stories[p] = hn[:25] + arx[:5]

    # 4. generate posts
    generated = 0
    for pillar, config in PILLARS.items():
        result = generate_post(pillar, config, pillar_stories[pillar], pillar_stories)
        if result:
            generated += 1

    print("=" * 55, file=sys.stderr)
    log(f"Koniec potoku. Wygenerowano {generated} nowych postów.")
    print("=" * 55, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
