#!/usr/bin/env python3
"""AcaciaFund — backfill historical daily posts."""

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
    "aml": {
        "FinCEN", "FATF", "SEC", "FCA", "ECB", "Fed", "OCC", "EBA",
        "Binance", "Coinbase", "Circle", "PayPal", "Stripe", "Block",
        "JPMorgan", "Goldman Sachs", "HSBC", "Deutsche Bank", "Citi",
        "Visa", "Mastercard", "SWIFT", "Pix", "FedNow",
    },
    "stock": {
        "NVIDIA", "AMD", "TSMC", "Intel", "ASML", "Apple", "Microsoft",
        "Samsung", "Qualcomm", "ARM", "Broadcom", "Micron", "Amazon",
        "Google", "Meta", "Tesla", "OpenAI", "SoftBank",
    },
    "science": {
        "OpenAI", "DeepMind", "Google AI", "Meta AI", "Anthropic", "xAI",
        "MIT", "Stanford", "Harvard", "Oxford", "Cambridge", "Caltech",
        "DARPA", "NIH", "CERN", "NASA", "ESA", "WHO",
    },
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

def extract_themes_from_post(text: str) -> list[str]:
    m = re.search(r"Dominujące wątki: \*\*(.+?)\*\*", text)
    if m:
        return [t.strip() for t in m.group(1).split(",")]
    return []

RULES_META = [
    {
        "name": "outlier_dominance",
        "match": lambda s: s.get("has_outlier") and s.get("score_skew") == "outlier",
        "generate": lambda s, stories, pname: (
            f"Uwagę społeczności zdominował jeden sygnał: "
            f"„**{stories[0]['title']}**” ({stories[0]['points']}⭐) — "
            f"to {s['outlier_ratio']:.1f}x więcej niż średnia pozostałych. "
            f"Dominująca kategoria źródła: **{s['top_domain']}**. "
            f"Z perspektywy systemowej to klasyczny efekt kaskady informacyjnej: "
            f"wysoka gęstość sprzężenia zwrotnego wokół jednego bodźca wywołuje "
            f"nieliniową amplifikację sygnału."
        )
    },
    {
        "name": "high_diversity",
        "match": lambda s: s.get("domain_diversity", 0) >= 4 and s.get("count", 0) >= 10,
        "generate": lambda s, stories, pname: (
            f"Zarejestrowano {s['count']} sygnałów z **{s['domain_diversity']} różnych kategorii źródeł** "
            f"({', '.join(k for k, v in Counter([categorize_domain(extract_domain(x.get('url',''))) for x in stories]).most_common(3))}), "
            f"co wskazuje na wysoką entropię informacyjną. "
            f"Topowe encje: {', '.join(s['top_entities'][:4]) or 'brak rozpoznawalnych'}. "
            f"Taka dyfuzja źródeł sugeruje, że zjawisko ma charakter systemowy, "
            f"a nie lokalny — rezonuje w różnych warstwach ekosystemu."
        )
    },
    {
        "name": "entity_cluster",
        "match": lambda s: s.get("entity_coherence") == "high" and s.get("count", 0) >= 5,
        "generate": lambda s, stories, pname: (
            f"Wysoka spójność encji ({', '.join(s['top_entities'][:3])}) przy "
            f"{s['count']} artykułach świadczy o krystalizacji narracji wokół "
            f"konkretnych podmiotów. System osiąga punkt krytyczny, w którym "
            f"lokalne fluktuacje synchronizują się w emergentny wzorzec. "
            f"To faza przejściowa — kolejne okno pokaże, czy trend się ustabilizuje."
        )
    },
    {
        "name": "low_volume",
        "match": lambda s: s.get("count", 0) <= 3 and s.get("count", 0) > 0,
        "generate": lambda s, stories, pname: (
            f"Niska gęstość sygnałów ({s['count']} artykułów) przy "
            f"{'wysokiej' if s['max_score'] > 100 else 'niskiej'} punktacji "
            f"(max {s['max_score']}⭐) sugeruje niszowy, ale "
            f"{'potencjalnie znaczący' if s['max_score'] > 100 else 'wyspecjalizowany'} "
            f"obszar dyskusji. W teorii systemów to okres ciszy przed "
            f"ewentualną kaskadą — mała liczba agentów, wysoka energia sygnału."
        )
    },
    {
        "name": "balanced_activity",
        "match": lambda s: s.get("score_skew") == "balanced" and s.get("count", 0) > 3,
        "generate": lambda s, stories, pname: (
            f"Zrównoważony rozkład punktacji ({s['count']} artykułów, "
            f"średnia {s['avg_score']:.0f}⭐, max {s['max_score']}⭐) wskazuje na "
            f"dojrzałą dyskusję bez dominującego sygnału. "
            f"Topowe encje: {', '.join(s['top_entities'][:3]) or 'różnorodne'}. "
            f"Źródła z domeny **{s['top_domain']}** stanowią "
            f"{s['top_domain_share']*100:.0f}% wszystkich. "
            f"To ekosystem o wysokiej różnorodności — stabilny, ale podatny na "
            f"zakłócenia zewnętrzne."
        )
    },
    {
        "name": "generic_high",
        "match": lambda s: s.get("count", 0) > 0,
        "generate": lambda s, stories, pname: (
            f"W obszarze {PILLARS[pname]['description'].lower()} odnotowano "
            f"{s['count']} artykułów (łączna pula {s['total_score']}⭐, "
            f"średnia {s['avg_score']:.0f}⭐). "
            f"Najwyżej oceniony: „**{stories[0]['title']}**” ({stories[0]['points']}⭐). "
            f"Dominująca kategoria źródła: **{s['top_domain']}**. "
            f"Tematy wiodące: {', '.join(s['top_entities'][:3]) or 'różnorodne'}."
        )
    },
]

RULES_SYSTEMS = [
    {
        "name": "outlier_cascade",
        "match": lambda s: s.get("has_outlier") and s.get("max_score", 0) > 300,
        "generate": lambda s, stories, pname: (
            f"Mechanizm kaskady informacyjnej: sygnał outlierowy ({stories[0]['points']}⭐) "
            f"uruchomił pętlę dodatniego sprzężenia zwrotnego — im więcej osób "
            f"interagowało z treścią, tym wyżej algorytm HN ją wyniósł, "
            f"generując dalszą ekspozycję. Z perspektywy cybernetycznej to "
            f"przykład eskalacji bez homeostazy: system nie miał wbudowanego "
            f"tłumika, który zrównoważyłby tę pętlę w czasie rzeczywistym. "
            f"Konsekwencje: {', '.join(s['top_entities'][:2]) or 'temat'} "
            f"może podlegać przeszacowaniu w kolejnych cyklach."
        )
    },
    {
        "name": "entropy_diversity",
        "match": lambda s: s.get("domain_diversity", 0) >= 4,
        "generate": lambda s, stories, pname: (
            f"Wysoka różnorodność źródeł ({s['domain_diversity']} kategorii) "
            f"świadczy o rozproszonej generacji informacji — system nie ma "
            f"centralnego agregatora, a emergentne wzorce powstają "
            f"z lokalnych interakcji na peryferiach sieci. "
            f"Zgodnie z drugą zasadą termodynamiki, wzrost entropii "
            f"informacyjnej zmniejsza zdolność systemu do predykcji — "
            f"ale zwiększa jego antykruchość poprzez redundancję "
            f"ścieżek sygnałowych."
        )
    },
    {
        "name": "coherence_phase",
        "match": lambda s: s.get("entity_coherence") == "high",
        "generate": lambda s, stories, pname: (
            f"Krystalizacja narracji wokół {', '.join(s['top_entities'][:3])} "
            f"to klasyczny obraz przejścia fazowego w systemie złożonym: "
            f"lokalne fluktuacje (pojedyncze artykuły) osiągają masę krytyczną, "
            f"po czym następuje synchronizacja faz. W tym momencie system "
            f"znajduje się w stanie krytycznym — drobny impuls może "
            f"przechylić równowagę w kierunku nowego attractora."
        )
    },
    {
        "name": "low_signal",
        "match": lambda s: s.get("count", 0) <= 3 and s.get("count", 0) > 0,
        "generate": lambda s, stories, pname: (
            f"Niska gęstość sygnałów przy jednoczesnej obecności tematów "
            f"({', '.join(s['top_entities'][:3]) or 'różnorodne'}) sugeruje "
            f"stan przed-krytyczny: system kumuluje energię potencjalną, "
            f"która może zostać uwolniona w kolejnym oknie obserwacji. "
            f"W cybernetyce nazywamy to histerezą — opóźnioną odpowiedzią "
            f"na bodziec poniżej progu aktywacji."
        )
    },
    {
        "name": "balanced_stable",
        "match": lambda s: s.get("score_skew") == "balanced" and s.get("count", 4) >= 4,
        "generate": lambda s, stories, pname: (
            f"Zrównoważony przepływ informacji ({s['count']} artykułów, "
            f"skew ratio {s['outlier_ratio']:.1f}) wskazuje na stan "
            f"homeostazy systemu. Pętle ujemnego sprzężenia zwrotnego "
            f"skutecznie tłumią odchylenia, utrzymując system w basenie "
            f"attractora. Z punktu widzenia antykruchości jest to "
            f"oznaka zdrowej redundancji — wiele słabych sygnałów "
            f"zamiast jednego dominującego."
        )
    },
    {
        "name": "generic_systems",
        "match": lambda s: s.get("count", 0) > 0,
        "generate": lambda s, stories, pname: (
            f"Analiza {s['count']} sygnałów w filarze {pname.upper()} "
            f"ujawnia strukturę sieci o gęstości "
            f"{'wysokiej' if s['count'] > 15 else 'średniej' if s['count'] > 5 else 'niskiej'}. "
            f"Najsilniejszy węzeł: „{stories[0]['title']}” ({stories[0]['points']}⭐) "
            f"z domeny {categorize_domain(extract_domain(stories[0].get('url','')))}. "
            f"Rozkład przypomina sieć bezskalową — kilka węzłów skupia "
            f"większość połączeń, reszta tworzy długi ogon dystrybucji."
        )
    },
]

RULES_CONN = [
    {
        "name": "shared_entities",
        "match": lambda cp: cp is not None and len(cp.get("shared_entities", [])) > 0,
        "generate": lambda cp, all_stories, pname: (
            f"Encja **{cp['shared_entities'][0]}** pojawiła się dziś zarówno w "
            f"filarze **{cp['pair'][0].upper()}** jak i **{cp['pair'][1].upper()}** "
            f"— realne cross-pillar połączenie. "
            f"W filarze {pname.upper()} dotyczy to artykułu "
            f"„{cp['article_a'][:80]}”. "
            f"Z punktu widzenia teorii systemów, obecność tej samej encji "
            f"w dwóch niezależnych domenach świadczy o istnieniu ukrytego "
            f"połączenia strukturalnego — być może wspólnego źródła zakłóceń "
            f"lub globalnego trendu, który manifestuje się lokalnie "
            f"w różnych subsystemach."
        )
    },
    {
        "name": "pillar_synergy",
        "match": lambda cp: cp is not None and cp.get("strength", 0) > 0,
        "generate": lambda cp, all_stories, pname: (
            f"Przekrój tematyczny łączy filary {cp['pair'][0].upper()} i "
            f"{cp['pair'][1].upper()} poprzez wspólne wątki "
            f"({' — '.join(cp['shared_entities'][:2])}). "
            f"Z perspektywy multi-domenowej AcaciaFund, te same sygnały "
            f"przetwarzane są przez różne warstwy abstrakcji — regulacyjną "
            f"(AML), kapitałową (Markets) i poznawczą (Science). "
            f"Rezonans między nimi amplifikuje znaczenie sygnału."
        )
    },
    {
        "name": "no_connection",
        "match": lambda cp: True,
        "generate": lambda cp, all_stories, pname: (
            f"W tym oknie czasowym nie wykryto silnych korelacji między "
            f"filarami na poziomie encji. Z perspektywy multi-domenowej "
            f"AcaciaFund, niezależność domen jest równie wartościowa — "
            f"oznacza, że systemy peryferyjne nie są nadmiernie "
            f"sprzężone, co zwiększa ogólną antykruchość portfela "
            f"informacyjnego."
        )
    },
]


def log(msg: str, ok: bool = True) -> None:
    prefix = "[+]" if ok else "[-]"
    print(f"{prefix} {msg}", file=sys.stderr)


def extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else ""


def classify_story(story: dict) -> list[tuple[str, int]]:
    title = story.get("title", "").lower()
    url = story.get("url", "")
    domain = extract_domain(url)
    scores: list[tuple[str, int]] = []
    for pillar_name, config in PILLARS.items():
        score = 0
        for dom_pattern, dom_score in config["domain_scores"].items():
            if dom_pattern in domain:
                score += dom_score
        for kw in config["keywords"]:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, title):
                score += 3
        if score > 0:
            scores.append((pillar_name, score))
    return scores


def fetch_stories_for_date(target_date: datetime, min_points: int = 2, max_hits: int = 1000) -> list[dict]:
    day_start = int(target_date.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc).timestamp())
    day_end = int((target_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)).timestamp())
    params = {
        "query": "",
        "tags": "story",
        "hitsPerPage": max_hits,
        "numericFilters": f"created_at_i>={day_start},created_at_i<={day_end}",
    }
    url = f"{ALGOLIA_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        log(f"Błąd pobierania HN dla {target_date.date()}: {e}", ok=False)
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
    words = []
    for t in titles:
        cleaned = re.sub(r"[^a-z\s]", " ", t.lower())
        words.extend(w for w in cleaned.split() if len(w) > 3 and w not in STOP_WORDS)
    counts = Counter(words)
    return [w.capitalize() for w, _ in counts.most_common(5)]


def apply_rules(rules: list[dict], signals: dict, stories: list[dict], pname: str, extra: any = None) -> str:
    for rule in rules:
        if rule["match"](signals if extra is None else extra):
            return rule["generate"](signals if extra is None else extra, stories, pname)
    return ""

def extract_themes_from_post(text: str) -> list[str]:
    m = re.search(r"Dominujące wątki: \*\*(.+?)\*\*", text)
    if m:
        return [t.strip() for t in m.group(1).split(",")]
    return []

def build_analysis(stories: list[dict], pillar_name: str,
                   all_pillar_stories: dict[str, list[dict]] | None = None) -> dict[str, str]:
    if not stories:
        return {
            "trending": f"*Brak doniesień z tego okresu dla tego obszaru.*\n\n*Pipeline AcaciaFund kontynuuje skanowanie.*",
            "metaanalysis": "Brak danych do analizy w tym oknie czasowym.",
            "systems_lens": "Brak sygnałów. Z punktu widzenia teorii systemów, brak informacji to również informacja.",
            "connections": "Brak korelacji w tym oknie czasowym.",
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
                cp_signal = {
                    "pair": (pillar_name, p),
                    "shared_entities": list(shared),
                    "strength": len(shared),
                    "article_a": a_in_p,
                }
                break

    conn = apply_rules(RULES_CONN, signals, stories, pillar_name, cp_signal)
    if not conn:
        conn = apply_rules([RULES_CONN[-1]], signals, stories, pillar_name, cp_signal)

    return {
        "trending": trending,
        "metaanalysis": meta,
        "systems_lens": systems,
        "connections": conn,
    }


def generate_post(pillar_name: str, config: dict, pillar_stories: list[dict], date: datetime,
                  all_pillar_stories: dict[str, list[dict]] | None = None) -> Path | None:
    date_str = date.strftime("%Y-%m-%d")
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
        f"## 🔍 Trending (HackerNews, {date_str})",
        "",
        analysis["trending"],
        "",
        '<div class="insight" style="border-left-color:var(--gold)">',
        '<h3 style="font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--gold);margin:0 0 8px">⚡ Kluczowe</h3>',
        f"<p>{max_score} ⭐ to najwyższa ocena w tym oknie. Średnia: {avg_score} ⭐. Łącznie {total_score} ⭐ z {link_count} linków.</p>",
        "</div>",
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
        f"*Raport wygenerowano {date_str}. Źródło: Algolia HN API. Klasyfikacja: AcaciaFund NLP.*",
    ]
    config["folder"].mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Wygenerowano: {filepath.relative_to(BASE_DIR)} ({link_count} linków)")
    return filepath


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Backfill historical AcaciaFund posts")
    parser.add_argument("--days", type=int, default=30, help="Liczba dni wstecz (domyślnie 30)")
    args = parser.parse_args()

    today = datetime.now(timezone.utc)
    print("=" * 55, file=sys.stderr)
    log(f"AcaciaFund Backfill — {args.days} dni wstecz od {today.strftime('%Y-%m-%d')}")
    print("=" * 55, file=sys.stderr)

    total_generated = 0
    for day_offset in range(args.days, 0, -1):
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")
        log(f"\n--- Przetwarzanie: {date_str} ---")

        stories = fetch_stories_for_date(target_date, min_points=2)
        if not stories:
            log(f"Brak danych dla {date_str} — pomijam", ok=False)
            continue
        log(f"Pobrano {len(stories)} stories dla {date_str}")

        pillar_stories: dict[str, list[dict]] = {p: [] for p in PILLARS}
        unclassified = 0
        for story in stories:
            classifications = classify_story(story)
            if not classifications:
                unclassified += 1
                continue
            best_pillar = max(classifications, key=lambda x: x[1])
            pillar_stories[best_pillar[0]].append(story)

        log(f"Skategoryzowano: AML={len(pillar_stories['aml'])}, STOCK={len(pillar_stories['stock'])}, SCIENCE={len(pillar_stories['science'])}, nieskategoryzowane={unclassified}")

        for pillar, config in PILLARS.items():
            ps = pillar_stories[pillar]
            ps.sort(key=lambda s: s["points"], reverse=True)
            pillar_stories[pillar] = ps[:30]

        for pillar, config in PILLARS.items():
            result = generate_post(pillar, config, pillar_stories[pillar], target_date,
                                   all_pillar_stories=pillar_stories)
            if result:
                total_generated += 1

    print("=" * 55, file=sys.stderr)
    log(f"Backfill zakończony. Wygenerowano {total_generated} nowych postów.")
    print("=" * 55, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
