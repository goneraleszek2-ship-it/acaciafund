import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content" / "daily"

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
USER_AGENT = "AcaciaFund/3.0"
HN_DISCUSSION_URL = "https://news.ycombinator.com/item?id={}"

PILLARS = {
    "aml": {
        "label": "AML", "emoji": "🛡️",
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
        "label": "STOCK", "emoji": "📈",
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
        "label": "SCIENCE", "emoji": "🧬",
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

# ── prekompilowane regexy dla classify_story ──
DOMAIN_PATTERNS = {}
for pname, config in PILLARS.items():
    DOMAIN_PATTERNS[pname] = [(re.compile(re.escape(d)), s) for d, s in config["domain_scores"].items()]

KEYWORD_PATTERNS = {}
for pname, config in PILLARS.items():
    KEYWORD_PATTERNS[pname] = [re.compile(rf"\b{re.escape(kw)}\b", re.I) for kw in config["keywords"]]

# ── RULES ──
RULES_META = [
    {"name": "outlier_dominance", "match": lambda s: s.get("has_outlier") and s.get("score_skew") == "outlier", "generate": lambda s, stories, pname: (f"Uwagę społeczności zdominował jeden sygnał: „**{stories[0]['title']}**” ({stories[0]['points']}⭐) — to {s['outlier_ratio']:.1f}x więcej niż średnia pozostałych. Dominująca kategoria źródła: **{s['top_domain']}**. Z perspektywy systemowej to klasyczny efekt kaskady informacyjnej: wysoka gęstość sprzężenia zwrotnego wokół jednego bodźca wywołuje nieliniową amplifikację sygnału.")},
    {"name": "high_diversity", "match": lambda s: s.get("domain_diversity", 0) >= 4 and s.get("count", 0) >= 10, "generate": lambda s, stories, pname: (f"Zarejestrowano {s['count']} sygnałów z **{s['domain_diversity']} różnych kategorii źródeł**, co wskazuje na wysoką entropię informacyjną. Topowe encje: {', '.join(s['top_entities'][:4]) or 'brak rozpoznawalnych'}. Taka dyfuzja źródeł sugeruje, że zjawisko ma charakter systemowy, a nie lokalny — rezonuje w różnych warstwach ekosystemu.")},
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

def log(msg: str, ok: bool = True) -> None:
    prefix = "[+]" if ok else "[-]"
    print(f"{prefix} {msg}", file=sys.stderr)

def extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else ""

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

def extract_themes(titles: list[str]) -> list[str]:
    words = []
    for t in titles:
        cleaned = re.sub(r"[^a-z\s]", " ", t.lower())
        words.extend(w for w in cleaned.split() if len(w) > 3 and w not in STOP_WORDS)
    counts = Counter(words)
    return [w.capitalize() for w, _ in counts.most_common(5)]
