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

SOURCE_TIERS: list[tuple[re.Pattern, float]] = [
    (re.compile(r"(\.gov|\.edu|\.mil)$"), 1.0),
    (re.compile(r"(nature\.com|science\.org|cell\.com|pnas\.org|biorxiv\.org|arxiv\.org|quantamagazine\.org|scientificamerican\.com)"), 1.0),
    (re.compile(r"(bloomberg\.com|reuters\.com|wsj\.com|ft\.com|economist\.com|nytimes\.com|washingtonpost\.com|theguardian\.com|bbc\.com|apnews\.com)"), 0.9),
    (re.compile(r"(fincen\.gov|fatf-gafi\.org|fca\.org\.uk|sec\.gov|occ\.gov|bis\.org|ec\.europa\.eu)"), 1.0),
    (re.compile(r"(anandtech\.com|tomshardware\.com|semiengineering\.com|arstechnica\.com|techcrunch\.com|theverge\.com|wired\.com)"), 0.8),
    (re.compile(r"(seekingalpha\.com|marketwatch\.com|investopedia\.com|coindesk\.com|cointelegraph\.com)"), 0.6),
    (re.compile(r"(github\.com|gitlab\.com|stackoverflow\.com)"), 0.7),
    (re.compile(r"(medium\.com|substack\.com|wordpress\.com|blogspot\.com)"), 0.4),
    (re.compile(r"(twitter\.com|x\.com|reddit\.com|youtube\.com)"), 0.3),
    (re.compile(r"(nvidia\.com|tsmc\.com|asml\.com|intel\.com|amd\.com)"), 0.8),
]

# ── prekompilowane regexy dla classify_story ──
DOMAIN_PATTERNS = {}
for pname, config in PILLARS.items():
    DOMAIN_PATTERNS[pname] = [(re.compile(re.escape(d)), s) for d, s in config["domain_scores"].items()]

KEYWORD_PATTERNS = {}
for pname, config in PILLARS.items():
    KEYWORD_PATTERNS[pname] = [re.compile(rf"\b{re.escape(kw)}\b", re.I) for kw in config["keywords"]]



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
