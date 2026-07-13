#!/usr/bin/env python3
"""Fix content quality issues in registry.json.

Handles:
1. Placeholder slugs → proper topic-based slugs
2. Markdown descriptions → clean text
3. Body HTML markdown → proper HTML
4. Same-pillar duplicates → remove knowledge versions
5. Difficulty backfill
6. Tag enrichment
"""

import json
import re
import unicodedata
from pathlib import Path

REGISTRY = Path(__file__).parent.parent / "registry.json"


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    text = text.strip('-')
    # Truncate to reasonable length
    if len(text) > 60:
        text = text[:60].rsplit('-', 1)[0]
    return text


def generate_slug_from_title(title: str, pillar: str, content_type: str) -> str:
    """Generate a proper slug from the item title."""
    # Clean title: remove emoji, date suffixes, source prefixes
    clean = re.sub(r'[\U0001f300-\U0001f9ff]', '', title)
    clean = re.sub(r'--\s*$', '', clean).strip()
    clean = re.sub(r'\d{4}-\d{2}-\d{2}$', '', clean).strip()
    clean = re.sub(r'\s*$', '', clean).strip()
    # Remove source prefixes like "Trending (HackerNews, ...)"
    clean = re.sub(r'^🔍\s*Trending.*?\)\s*', '', clean)
    clean = re.sub(r'^Trending.*?\)\s*', '', clean)
    clean = re.sub(r'^SCIENCE\s*', '', clean)
    clean = re.sub(r'^STOCK\s*', '', clean)
    clean = re.sub(r'^AML\s*', '', clean)
    
    topic = slugify(clean)
    if not topic:
        topic = "article"
    
    return f"{pillar}/{content_type}/{topic}"


def fix_slug(slug: str, title: str, pillar: str, content_type: str) -> str:
    """Fix placeholder slugs."""
    parts = slug.split('/')
    if len(parts) >= 3 and parts[-1] in ('aml', 'stock', 'science', 'science-1'):
        new_slug = generate_slug_from_title(title, parts[0], parts[1])
        return new_slug
    return slug


def clean_description(desc: str) -> str:
    """Remove markdown formatting from descriptions."""
    if not desc:
        return desc
    # Remove **bold**
    desc = re.sub(r'\*\*(.+?)\*\*', r'\1', desc)
    # Remove *italic*
    desc = re.sub(r'\*(.+?)\*', r'\1', desc)
    # Remove [link](url)
    desc = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', desc)
    # Remove leading markdown headers
    desc = re.sub(r'^#+\s*', '', desc)
    # Remove emoji prefixes
    desc = re.sub(r'^[🔍🛡️📈📊💡🎯✅❌⚠️]+\s*', '', desc)
    # Clean up extra whitespace
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc


def convert_markdown_in_html(html: str) -> str:
    """Convert markdown patterns in body_html to proper HTML."""
    if not html:
        return html
    
    # Handle code fences first (before other conversions)
    def replace_code_fences(m):
        lang = m.group(1) or ''
        code = m.group(2)
        return f'<pre><code class="language-{lang}">{code}</code></pre>'
    
    html = re.sub(r'```(\w*)\n(.*?)```', replace_code_fences, html, flags=re.DOTALL)
    
    # Handle headings (only outside <pre> tags)
    def replace_headings_outside_pre(text):
        # Split by <pre> tags to process only non-pre content
        parts = re.split(r'(<pre>.*?</pre>)', text, flags=re.DOTALL)
        result = []
        for i, part in enumerate(parts):
            if part.startswith('<pre>'):
                result.append(part)
            else:
                # Convert markdown headings to HTML
                part = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', part, flags=re.MULTILINE)
                part = re.sub(r'^### (.+)$', r'<h3>\1</h3>', part, flags=re.MULTILINE)
                part = re.sub(r'^## (.+)$', r'<h2>\1</h2>', part, flags=re.MULTILINE)
                part = re.sub(r'^# (.+)$', r'<h1>\1</h1>', part, flags=re.MULTILINE)
                result.append(part)
        return ''.join(result)
    
    html = replace_headings_outside_pre(html)
    
    # Handle bold and italic (outside pre tags)
    def replace_inline_outside_pre(text):
        parts = re.split(r'(<pre>.*?</pre>)', text, flags=re.DOTALL)
        result = []
        for part in parts:
            if part.startswith('<pre>'):
                result.append(part)
            else:
                part = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', part)
                part = re.sub(r'\*(.+?)\*', r'<em>\1</em>', part)
                result.append(part)
        return ''.join(result)
    
    html = replace_inline_outside_pre(html)
    
    return html


def get_difficulty(sqi: float, content_type: str) -> str:
    """Determine difficulty based on SQI and content type."""
    if content_type == 'knowledge':
        return 'advanced'
    if content_type == 'learn':
        if sqi >= 0.9:
            return 'advanced'
        elif sqi >= 0.75:
            return 'intermediate'
        else:
            return 'beginner'
    # research
    if sqi >= 0.9:
        return 'advanced'
    elif sqi >= 0.75:
        return 'intermediate'
    else:
        return 'beginner'


def extract_concepts_for_tags(title: str, description: str, body: str, ontology_concepts: list) -> list:
    """Extract relevant tags from content."""
    tags = set()
    
    # Add ontology concepts as tags
    for concept in ontology_concepts:
        tags.add(concept.lower().replace(' ', '-').replace('/', '-'))
    
    # Extract from title keywords
    title_lower = title.lower()
    keyword_map = {
        'machine learning': 'machine-learning',
        'deep learning': 'deep-learning',
        'neural network': 'neural-networks',
        'data pipeline': 'data-pipelines',
        'data quality': 'data-quality',
        'data governance': 'data-governance',
        'real-time': 'real-time',
        'streaming': 'streaming',
        'kafka': 'kafka',
        'spark': 'spark',
        'airflow': 'airflow',
        'dbt': 'dbt',
        'snowflake': 'snowflake',
        'databricks': 'databricks',
        'aml': 'aml',
        'kyc': 'kyc',
        'sanctions': 'sanctions',
        'compliance': 'compliance',
        'trading': 'trading',
        'portfolio': 'portfolio',
        'risk': 'risk',
        'market': 'markets',
        'stock': 'stock-market',
        'fintech': 'fintech',
        'blockchain': 'blockchain',
        'crypto': 'cryptocurrency',
        'cloud': 'cloud',
        'aws': 'aws',
        'gcp': 'gcp',
        'azure': 'azure',
        'python': 'python',
        'sql': 'sql',
        'api': 'api',
        'microservices': 'microservices',
        'devops': 'devops',
        'ci/cd': 'cicd',
        'monitoring': 'monitoring',
        'analytics': 'analytics',
        'visualization': 'data-visualization',
        'etl': 'etl',
        'elt': 'elt',
        'data warehouse': 'data-warehouse',
        'data lake': 'data-lake',
        'data lakehouse': 'data-lakehouse',
        'feature store': 'feature-store',
        'ml ops': 'mlops',
        'mlops': 'mlops',
    }
    
    text = f"{title_lower} {description.lower()}"
    for keyword, tag in keyword_map.items():
        if keyword in text:
            tags.add(tag)
    
    # Add pillar as tag
    return list(tags)[:10]  # Limit to 10 tags


def main():
    with open(REGISTRY) as f:
        reg = json.load(f)
    
    content = reg['content']
    changes = {
        'slugs_fixed': 0,
        'descriptions_cleaned': 0,
        'body_html_converted': 0,
        'duplicates_removed': 0,
        'difficulty_backfilled': 0,
        'tags_enriched': 0,
    }
    
    # Track used slugs to avoid collisions
    used_slugs = set()
    for item in content:
        used_slugs.add(item.get('slug', ''))
    
    # STEP 1: Fix placeholder slugs and clean descriptions
    print("Step 1: Fixing placeholder slugs and descriptions...")
    for item in content:
        slug = item.get('slug', '')
        title = item.get('title', '')
        pillar = item.get('pillar', '')
        content_type = item.get('content_type', '')
        
        # Fix slug
        new_slug = fix_slug(slug, title, pillar, content_type)
        if new_slug != slug:
            # Ensure uniqueness
            base_slug = new_slug
            counter = 1
            while new_slug in used_slugs:
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            item['slug'] = new_slug
            used_slugs.add(new_slug)
            changes['slugs_fixed'] += 1
            print(f"  Slug: {slug} -> {new_slug}")
        
        # Clean description
        desc = item.get('description', '')
        new_desc = clean_description(desc)
        if new_desc != desc:
            item['description'] = new_desc
            changes['descriptions_cleaned'] += 1
    
    # STEP 2: Convert body HTML markdown
    print("\nStep 2: Converting body HTML markdown...")
    for item in content:
        body = item.get('body_html', '')
        if not body:
            continue
        new_body = convert_markdown_in_html(body)
        if new_body != body:
            item['body_html'] = new_body
            changes['body_html_converted'] += 1
    
    # STEP 3: Remove same-pillar duplicates (keep learn, remove knowledge)
    print("\nStep 3: Removing same-pillar duplicates...")
    from collections import defaultdict
    title_pillar = defaultdict(list)
    for item in content:
        key = (item.get('title', ''), item.get('pillar', ''))
        title_pillar[key].append(item)
    
    slugs_to_remove = set()
    for (title, pillar), items in title_pillar.items():
        if len(items) <= 1:
            continue
        # Keep learn version, remove knowledge version
        learn_items = [i for i in items if i.get('content_type') == 'learn']
        knowledge_items = [i for i in items if i.get('content_type') == 'knowledge']
        if learn_items and knowledge_items:
            for ki in knowledge_items:
                slugs_to_remove.add(ki.get('slug', ''))
                print(f"  Removing duplicate: {ki.get('slug', '')}")
    
    content = [item for item in content if item.get('slug', '') not in slugs_to_remove]
    changes['duplicates_removed'] = len(slugs_to_remove)
    
    # STEP 4: Backfill difficulty
    print("\nStep 4: Backfilling difficulty...")
    for item in content:
        if not item.get('difficulty'):
            sqi = item.get('sqi', 0.75)
            content_type = item.get('content_type', 'research')
            item['difficulty'] = get_difficulty(sqi, content_type)
            changes['difficulty_backfilled'] += 1
    
    # STEP 5: Enrich tags
    print("\nStep 5: Enriching tags...")
    for item in content:
        tags = item.get('tags', [])
        if len(tags) < 3:
            title = item.get('title', '')
            desc = item.get('description', '')
            body = item.get('body_html', '')
            concepts = item.get('ontology_concepts', [])
            new_tags = extract_concepts_for_tags(title, desc, body, concepts)
            # Merge with existing tags
            all_tags = list(set(tags + new_tags))
            if len(all_tags) > len(tags):
                item['tags'] = all_tags[:10]
                changes['tags_enriched'] += 1
    
    reg['content'] = content
    
    # Save
    with open(REGISTRY, 'w') as f:
        json.dump(reg, f, indent=2)
    
    print("\n=== SUMMARY ===")
    for k, v in changes.items():
        print(f"  {k}: {v}")
    print(f"\nFinal item count: {len(content)}")


if __name__ == '__main__':
    main()
