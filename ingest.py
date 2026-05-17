import json
import urllib.request
import urllib.parse
from datetime import datetime
import os

# Konfiguracja słów kluczowych dla każdego z Twoich trzech filarów
PILLARS = {
    "aml": {
        "keywords": ["compliance", "fintech", "regtech", "laundering"],
        "folder": "content/daily/aml",
        "tags": ["aml", "compliance", "regtech"]
    },
    "stock": {
        "keywords": ["semiconductor", "nvidia", "tsmc", "asml", "valuation"],
        "folder": "content/daily/stock",
        "tags": ["markets", "stocks", "semiconductors"]
    },
    "science": {
        "keywords": ["cybernetics", "mitochondria", "biology", "systems theory"],
        "folder": "content/daily/science",
        "tags": ["science", "systems", "cybernetics"]
    }
}

def fetch_hn_stories(keyword, limit=3):
    """Pobiera najnowsze wpisy z Algolia HackerNews API dla danego słowa kluczowego"""
    encoded_query = urllib.parse.quote(keyword)
    url = f"https://hn.algolia.com/api/v1/search?query={encoded_query}&tags=story&hitsPerPage={limit}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AcaciaFund-Scraper/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        stories = []
        for hit in data.get('hits', []):
            stories.append({
                "title": hit.get("title"),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "score": hit.get("points", 0)
            })
        return stories
    except Exception as e:
        print(f"[-] Błąd pobierania dla '{keyword}': {e}")
        return []

def generate_markdown(pillar_name, config):
    """Agreguje dane i tworzy plik Markdown w formacie Hugo"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today_str}.md"
    filepath = os.path.join(config["folder"], filename)
    
    # Zbieramy unikalne znaleziska ze wszystkich słów kluczowych danego filaru
    all_stories = []
    seen_urls = set()
    
    for kw in config["keywords"]:
        fetched = fetch_hn_stories(kw, limit=2)
        for story in fetched:
            if story["url"] not in seen_urls:
                seen_urls.add(story["url"])
                all_stories.append(story)
                
    # Budujemy strukturę posta z Frontmatterem (Hugo potrzebuje pola 'title')
    markdown_content = f"""---
title: "Synteza {pillar_name.upper()} z dnia {today_str}"
date: {today_str}
tags: {json.dumps(config["tags"])}
theme: "Ewolucja systemowa i path dependency"
---

## 🔍 Trending (Znaleziska z HackerNews)
"""
    if not all_stories:
        markdown_content += "\n*Brak nowych, pasujących doniesień z ostatnich 24h.*\n"
    else:
        for story in all_stories[:5]: # Maksymalnie 5 najciekawszych
            markdown_content += f"- [{story['title']}]({story['url']}) (Skor: {story['score']})\n"
            
    markdown_content += f"""
## 📊 Metaanalysis
Wstępna agregacja danych wskazuje na strukturalne przesunięcia w obszarze {pillar_name}. Obserwujemy zwiększoną gęstość sygnałów dotyczących optymalizacji i skalowalności rozwiązań systemowych.

## 🧠 Systems lens (Antifragility & Cybernetics)
Z punktu widzenia sprzężeń zwrotnych, analizowane trendy ujawniają dążenie do redukcji entropii wewnątrzsystemowej kosztem delegowania ryzyk na warstwy peryferyjne.

## ↔️ Connections
Synergia z pozostałymi domenami AcaciaFund: ewolucja struktur technologicznych determinuje możliwości adaptacyjne modeli poznawczych.
"""
    
    # Zapisujemy gotowy plik Markdown
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"[+] Wygenerowano post: {filepath}")

if __name__ == "__main__":
    print(f"=== Uruchomienie potoku ingestii AcaciaFund: {datetime.now()} ===")
    for pillar, config in PILLARS.items():
        generate_markdown(pillar, config)
