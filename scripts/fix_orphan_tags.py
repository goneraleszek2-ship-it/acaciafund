"""Fix orphan tags and conflicting aliases in the AcaciaFund ontology.

Usage:
    python3 scripts/fix_orphan_tags.py
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.json"
ONTOLOGY_PATH = ROOT / "data/ontology.json"
PHILOSOPHY_PATH = ROOT / "data/philosophy_metadata.json"


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def normalize(s: str) -> str:
    return s.lower().replace('-', ' ').strip()


def title_case(tag: str) -> str:
    return ' '.join(word.capitalize() for word in tag.replace('-', ' ').split())


# ---------------------------------------------------------------------------
# KNOWN SYNONYMS — tags that map to a concept but whose string doesn't match
# any label / alias / id of that concept.
# ---------------------------------------------------------------------------
KNOWN_SYNONYMS = {
    "agentic-systems": "ai-act-high-risk",
    "ai": "ai-act-high-risk",
    "ai-automation": "ml-pipeline",
    "alphafold": "ml-pipeline",
    "aml": "aml-regulatory-framework",
    "aml-reporting": "regulatory-reporting",
    "aml-typologies": "fincrime-intelligence",
    "amla": "bsa",
    "analytics-engineering": "data-pipeline",
    "annual": "data-pipeline",
    "anthropic": "ai-act-high-risk",
    "anthropic-denied-s-p-500-entry": "ai-act-high-risk",
    "anti-money-laundering": "money-laundering-basics",
    "api": "data-contracts",
    "api-design": "data-contracts",
    "atmospheric": "data-pipeline",
    "attempt": "data-pipeline",
    "behavioral": "behavioral-finance",
    "behind": "data-pipeline",
    "benefits": "data-pipeline",
    "big-data-engineering": "data-pipeline",
    "big-data-migration": "data-pipeline",
    "big-data-storage": "data-lake",
    "bioinformatics-pipelines": "ml-pipeline",
    "biotech genomics": "ml-pipeline",
    "biotech-genomics": "ml-pipeline",
    "bun": "data-pipeline",
    "chemistry": "ml-pipeline",
    "claim": "data-pipeline",
    "cloud-architecture": "distributed-systems",
    "cloud-computing": "distributed-systems",
    "cloud-computing-optimization": "distributed-systems",
    "cloud-infrastructure": "distributed-systems",
    "complete-data-stack-deployment": "dataops",
    "compliance": "aml-compliance-basics",
    "computing": "distributed-systems",
    "container-orchestration": "orchestration",
    "continuous-integration": "dataops",
    "contract-versioning": "data-contract-testing",
    "corporate-finance": "equity-basics",
    "cost-engineering": "pipeline-cost-optimization",
    "cost-optimization": "pipeline-cost-optimization",
    "crypto": "crypto-markets",
    "crypto-finance": "crypto-markets",
    "customer-due-diligence": "cdd",
    "cybersecurity": "data-security",
    "data-architecture": "data-pipeline",
    "data-cataloging": "data-catalog",
    "data-engineering": "data-pipeline",
    "data-engineering-basics": "data-pipeline",
    "data-format-optimization": "arrow-parquet",
    "data-lake-engineering": "data-lake",
    "data-lake-management": "data-lake",
    "data-mesh-implementation": "data-mesh",
    "data-ops": "dataops",
    "data-pipeline-engineering": "data-pipeline",
    "data-pipeline-management": "data-pipeline",
    "data-pipeline-optimization": "data-pipeline",
    "data-pipeline-orchestration": "orchestration",
    "data-platform": "data-platform-kpis",
    "data-platform-on-budget": "data-cost-intelligence",
    "data-products": "data-mesh",
    "data-replication": "cdc",
    "data-serialization": "arrow-parquet",
    "data-transformation": "etl",
    "database-integration": "data-lake",
    "delta-lake": "lakehouse",
    "deprecated": "data-pipeline",
    "derivatives": "options-trading",
    "design": "software-architecture",
    "detects": "data-pipeline",
    "developer-experience": "dataops",
    "devops-practices": "dataops",
    "differential": "differential-privacy",
    "distributed-computing": "distributed-systems",
    "distributed-data-storage": "distributed-systems",
    "documentation": "model-cards",
    "domain-ownership-patterns": "data-mesh",
    "education": "data-pipeline",
    "effective": "data-pipeline",
    "enterprise-architecture": "data-architecture",
    "event-driven": "event-driven-trading",
    "event-driven-architecture": "event-driven-trading",
    "events": "event-driven-trading",
    "ever": "data-pipeline",
    "exoplanet": "data-pipeline",
    "fatf": "fatf-recommendations",
    "feature-engineering": "feature-store",
    "fed": "macro-analysis",
    "federated-governance": "data-mesh-governance",
    "finance": "equity-basics",
    "financial-crime": "financial-crime-types",
    "financial-crime-analytics": "fincrime-intelligence",
    "financial-technology": "regtech",
    "fincen": "fincen-boi",
    "fundamental-analysis": "macro-analysis",
    "funding": "startups",
    "genomics-workflows": "ml-pipeline",
    "geometry": "ml-pipeline",
    "habitable": "data-pipeline",
    "hardware": "ai-hardware",
    "implied-volatility": "volatility-surface",
    "incident-response-management": "data-observability",
    "infrastructure": "cloud-architecture",
    "infrastructure-as-code": "dataops",
    "internal-data-platform": "data-platform-kpis",
    "internal-product-development": "data-mesh",
    "introduction": "data-pipeline",
    "jwst": "data-pipeline",
    "knowledge": "data-catalog",
    "lakehouse-architecture": "lakehouse",
    "largest": "data-pipeline",
    "learn": "machine-learning-markets",
    "learning": "data-pipeline",
    "limited": "data-pipeline",
    "llm": "machine-learning-markets",
    "machine-learning": "ml-pipeline",
    "machine-learning-infrastructure": "ml-pipeline",
    "macro-economics": "macro-analysis",
    "manufacturing": "data-pipeline",
    "market-fundamentals": "equity-basics",
    "market-structure": "market-microstructure",
    "markets": "market-participants",
    "million": "data-pipeline",
    "model-deployment": "ml-pipeline",
    "model-serving": "ml-pipeline",
    "monitoring": "data-observability",
    "new": "data-pipeline",
    "now": "data-pipeline",
    "open-source-data-stack": "data-pipeline",
    "openai": "ai-act-high-risk",
    "openai-blocked-from-s-p-500": "ai-act-high-risk",
    "options": "options-trading",
    "pictorial": "data-pipeline",
    "pipeline-cost-optimization": "pipeline-cost-optimization",
    "pipeline-orchestration": "orchestration",
    "pipelines": "data-pipeline",
    "platform": "data-platform-kpis",
    "platforms": "data-platform-kpis",
    "portfolio": "portfolio-optimization",
    "predicts": "data-pipeline",
    "privacy-ethics": "gdpr-anonymization",
    "protein": "ml-pipeline",
    "python-engineering": "data-pipeline",
    "quantitative-finance": "quantitative-trading",
    "quantum": "distributed-systems",
    "rate": "macro-analysis",
    "reaches": "data-pipeline",
    "real-time-data-integration": "real-time-analytics",
    "real-time-data-processing": "real-time-analytics",
    "real-time-streaming": "streaming",
    "reasoning": "data-pipeline",
    "record": "data-pipeline",
    "regulations": "aml-regulatory-framework",
    "regulatory compliance": "aml-regulatory-framework",
    "replication": "cdc",
    "research": "signal-quality",
    "resource-management": "orchestration",
    "results": "data-pipeline",
    "risk-assessment": "risk-based-approach",
    "risk-management": "risk-based-approach",
    "room": "data-pipeline",
    "run": "data-pipeline",
    "runtime": "orchestration",
    "s-p-500-rejects-spacex": "equity-basics",
    "scalable-data-processing": "distributed-systems",
    "schema-evolution": "schema-registry",
    "schema-management": "schema-registry",
    "science": "data-pipeline",
    "scientific": "data-pipeline",
    "see": "data-pipeline",
    "self-service-analytics": "data-mesh",
    "semiconductors": "semiconductor-industry",
    "signal-quality": "data-quality-sla",
    "software-architecture": "data-pipeline",
    "software-quality": "data-quality",
    "spacex": "equity-basics",
    "startups": "market-participants",
    "stock": "equity-basics",
    "stock-market": "equity-basics",
    "stockmarket": "equity-basics",
    "stream-processing": "streaming",
    "streaming-data-processing": "streaming",
    "streaming-etl": "streaming",
    "supply-chain": "supply-chain-analysis",
    "swallow": "data-pipeline",
    "synthesis": "data-pipeline",
    "tariffs": "macro-analysis",
    "test-automation": "data-quality",
    "timeline": "data-pipeline",
    "trade-finance-crime": "trade-finance-aml",
    "trading": "algorithmic-trading",
    "ux-design-patterns": "data-architecture",
    "volatility": "volatility-surface",
    "workflow-automation": "orchestration",
    "workflow-orchestration": "orchestration",
    "securities-lending": "stock-lending",
    "commodity trading": "commodity-trading",
    "commodity-trading": "commodity-trading",
}


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {path}")


def build_concept_lookup(concepts):
    """Build lookup structures from ontology concepts.

    Returns:
        concept_by_id: dict id -> concept dict
        concept_by_label_lower: dict lowercase label -> concept dict
        all_labels_aliases_lower: set of all labels + aliases lowercased
    """
    concept_by_id = {}
    concept_by_label_lower = {}
    all_labels_aliases_lower = set()

    for c in concepts:
        cid = c['id']
        concept_by_id[cid] = c
        all_labels_aliases_lower.add(c['label'].lower())
        concept_by_label_lower[c['label'].lower()] = c
        for a in c.get('aliases', []):
            all_labels_aliases_lower.add(a.lower())

    return concept_by_id, concept_by_label_lower, all_labels_aliases_lower


def tag_matches_concept(tag, concept_id, concept, all_labels_aliases_lower):
    """Check if a tag matches a concept's label, aliases, or id (case-insensitive)."""
    t_lower = tag.lower()
    ntag = normalize(tag)

    label = concept['label'].lower()
    if t_lower == label or normalize(tag) == normalize(concept['label']):
        return True
    if t_lower == concept_id.lower() or normalize(tag) == normalize(concept_id):
        return True
    for a in concept.get('aliases', []):
        if t_lower == a.lower() or ntag == normalize(a):
            return True
    return False


def find_orphan_tags(all_tags, concept_by_id, all_labels_aliases_lower):
    """Find tags that don't directly match any concept label, alias, or id."""
    orphans = []
    for t in all_tags:
        # Check if tag matches any label, alias, or id
        matched = False
        for cid, c in concept_by_id.items():
            if tag_matches_concept(t, cid, c, all_labels_aliases_lower):
                matched = True
                break
        if not matched:
            orphans.append(t)
    return orphans


def auto_detect_pillar(tag, tag_pillar_counts):
    """Detect the most appropriate pillar for a novel tag."""
    if tag.startswith("data-") or tag.startswith("data "):
        return "data-engineering"
    if tag.startswith("aml-") or tag.startswith("aml "):
        return "aml"
    if tag.startswith("stock-") or tag.startswith("stock "):
        return "stock"
    if tag in tag_pillar_counts:
        counts = tag_pillar_counts[tag]
        return max(counts, key=counts.get)
    return "data-engineering"


def generate_new_concept(tag, pillar, tag_frequency):
    """Create a new concept dict for a genuinely novel tag."""
    cid = slugify(tag)
    label = title_case(tag)

    aliases_set = set()
    aliases_set.add(tag)
    aliases_set.add(tag.replace('-', ''))
    # Remove any alias that matches the label or ID
    aliases_final = [a for a in aliases_set if a != slugify(label)]
    if not aliases_final:
        aliases_final = [tag]

    return {
        "id": cid,
        "label": label,
        "description": f"A concept related to {tag}",
        "pillar": pillar,
        "category": "specialized",
        "aliases": aliases_final,
        "properties": {},
        "source_inspiration": "curated",
        "confidence_score": 0.7,
        "philosophical_lineage": [],
        "epistemic_status": "instrumental",
        "normative_basis": "",
        "ontological_commitment": "",
        "temporal_ontology": "",
        "uncertainty_class": "",
        "governance_model": "",
        "semantic_contract_type": "",
        "philosophical_sources": [],
        "cross_pillar_analogs": [],
    }


# ---------------------------------------------------------------------------
# CONFLICTING ALIAS RESOLUTION
# ---------------------------------------------------------------------------
def fix_conflicting_aliases(concepts, all_item_tag_lists):
    """Find aliases shared by multiple concepts and remove them from all but
    the most relevant concept.

    Returns count of removed aliases.
    """
    alias_to_concepts = defaultdict(list)
    for idx, c in enumerate(concepts):
        for a in c.get('aliases', []):
            alias_to_concepts[a.lower()].append((idx, c))

    conflicts = {a: entries for a, entries in alias_to_concepts.items() if len(entries) > 1}
    removed_count = 0

    for alias_lower, entries in sorted(conflicts.items()):
        indices = [e[0] for e in entries]
        concepts_list = [e[1] for e in entries]

        scores = []
        for c in concepts_list:
            score = 0
            clower = c['label'].lower()
            # Primary: label matches the alias
            if clower == alias_lower:
                score = 100
            # Secondary: alias appears in label
            elif alias_lower in clower or alias_lower.replace('-', ' ') in clower:
                score = 50
            # Tertiary: alias contains the label
            elif clower in alias_lower:
                score = 30
            else:
                # Count how many items reference this concept (by id or label prefix)
                cid = c['id']
                refs = 0
                for tag_set in all_item_tag_lists:
                    for t in tag_set:
                        if cid in t or normalize(cid) in normalize(t):
                            refs += 1
                            break
                score = refs
            scores.append(score)

        # Keep alias on highest-scored concept, remove from others
        best_idx = indices[scores.index(max(scores))]
        for idx in indices:
            if idx == best_idx:
                continue
            c = concepts[idx]
            to_remove = None
            for a in c.get('aliases', []):
                if a.lower() == alias_lower:
                    to_remove = a
                    break
            if to_remove:
                c['aliases'].remove(to_remove)
                removed_count += 1

    return removed_count


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("AcaciaFund — Orphan Tag & Alias Conflict Fixer")
    print("=" * 60)

    # 1. Load data
    print("\n[1] Loading data...")
    registry = load_json(REGISTRY_PATH)
    ontology = load_json(ONTOLOGY_PATH)
    philosophy = load_json(PHILOSOPHY_PATH)

    concepts = ontology['concepts']
    existing_ids = {c['id'] for c in concepts}

    # 2. Collect ALL tags from all 155 content items
    print("\n[2] Collecting tags from registry...")
    all_content = registry.get('content', [])
    print(f"  Content items: {len(all_content)}")

    tag_frequency = Counter()
    tag_pillar_counts = defaultdict(lambda: Counter())

    all_tags_set = set()
    for item in all_content:
        pillar = item.get('pillar', '')
        tags = item.get('tags', [])
        for t in tags:
            tag_frequency[t] += 1
            all_tags_set.add(t)
            tag_pillar_counts[t][pillar] += 1

    all_item_tag_lists = [set(t.lower() for t in item.get('tags', []))
                          for item in all_content]

    print(f"  Unique tags: {len(all_tags_set)}")

    # 3. Build concept lookup
    print("\n[3] Building concept lookup...")
    concept_by_id, concept_by_label_lower, all_labels_aliases_lower = \
        build_concept_lookup(concepts)
    print(f"  Existing concepts: {len(concepts)}")

    # 4. Find orphan tags (tags that match no label, alias, or id directly)
    print("\n[4] Finding orphan tags...")
    orphan_tags = find_orphan_tags(all_tags_set, concept_by_id, all_labels_aliases_lower)
    print(f"  Orphan tags: {len(orphan_tags)}")

    # 5. Attempt mapping: first by known synonyms, then by fuzzy match
    print("\n[5] Mapping orphan tags...")

    mapped_tags = {}  # tag -> (concept_id, method, added_as_alias)
    novel_tags = []

    for t in sorted(orphan_tags):
        t_lower = t.lower()

        # 5a. Known synonym mapping
        if t_lower in KNOWN_SYNONYMS or t in KNOWN_SYNONYMS:
            target_id = KNOWN_SYNONYMS.get(t_lower) or KNOWN_SYNONYMS.get(t)
            if target_id in concept_by_id:
                mapped_tags[t] = (target_id, "known-synonym", False)
                continue

        # 5b. Levenshtein distance ≤ 2 against concept labels
        best_cid = None
        best_dist = 3
        for c in concepts:
            dist = levenshtein(normalize(t), normalize(c['label']))
            if dist <= 2 and dist < best_dist:
                best_cid = c['id']
                best_dist = dist
        if best_cid:
            mapped_tags[t] = (best_cid, f"fuzzy(lev={best_dist})", False)
            continue

        # 5c. Prefix / overlap match (tag is prefix of label, or vice versa, length ≥ 4)
        for c in concepts:
            t_norm = normalize(t)
            l_norm = normalize(c['label'])
            if len(t_norm) >= 4 and len(l_norm) >= 4:
                if t_norm.startswith(l_norm) or l_norm.startswith(t_norm):
                    mapped_tags[t] = (c['id'], "prefix", False)
                    break
        if t in mapped_tags:
            continue

        # 5d. Remove hyphens and compare
        t_noh = t_lower.replace('-', '')
        for c in concepts:
            if t_noh == c['label'].lower().replace('-', ''):
                mapped_tags[t] = (c['id'], "nohyphen-label", False)
                break
            for a in c.get('aliases', []):
                if t_noh == a.lower().replace('-', ''):
                    mapped_tags[t] = (c['id'], "nohyphen-alias", False)
                    break
        if t in mapped_tags:
            continue

        # No mapping found — novel tag
        novel_tags.append(t)

    print(f"  Mapped to existing concepts: {len(mapped_tags)}")
    print(f"  Truly novel tags: {len(novel_tags)}")

    if mapped_tags:
        print("\n  Mapping details:")
        for t, (cid, method, _) in sorted(mapped_tags.items()):
            print(f"    {t:45s} -> {cid} ({method})")

    # 6. Add mapped tags as aliases to their target concepts, unless too short
    #    or already an alias. This ensures the mapping is persistent.
    print("\n[6] Adding mapped tags as concept aliases...")
    alias_additions = 0
    for t, (cid, method, _) in sorted(mapped_tags.items()):
        if len(t) < 3:
            continue
        c = concept_by_id[cid]
        existing_aliases_lower = [a.lower() for a in c.get('aliases', [])]
        # Don't add if it's too noisy (single common words)
        if t.lower() in ('ai', 'aml', 'crypto', 'stock', 'trading',
                         'finance', 'platform', 'portfolio', 'markets',
                         'research', 'learn', 'knowledge', 'design',
                         'events', 'options', 'hardware', 'science',
                         'funding', 'new', 'now', 'see', 'run', 'rate',
                         'record', 'ever', 'room', 'annual', 'million',
                         'results', 'benefits', 'effective', 'limited',
                         'attempt', 'claim', 'predicts', 'reasoning',
                         'learning', 'introduction', 'education',
                         'scientific', 'manufacturing', 'behind',
                         'swallow', 'pictorial', 'synthesis', 'bun',
                         'runtime', 'deprecated', 'detects',
                         'differential', 'behavioral', 'computing',
                         'monitoring', 'pipelines', 'replication',
                         'computing', 'largest', 'reaches'):
            continue
        if t.lower() not in existing_aliases_lower:
            c.setdefault('aliases', []).append(t)
            alias_additions += 1

    print(f"  Aliases added: {alias_additions}")

    # 6b. Also add aliases for tags that match via normalization (e.g. "customer-due-diligence"
    #     matches label "Customer Due Diligence" when normalized) but aren't exact matches.
    normalized_alias_additions = 0
    for t in sorted(all_tags_set):
        t_lower = t.lower()
        if t_lower in KNOWN_SYNONYMS or t in KNOWN_SYNONYMS:
            continue
        if len(t) < 4:
            continue
        if t_lower in all_labels_aliases_lower:
            continue
        for c in concepts:
            norm_matches = normalize(t) == normalize(c['label']) or \
                           normalize(t) == normalize(c['id'])
            if not norm_matches:
                for a in c.get('aliases', []):
                    if normalize(t) == normalize(a):
                        norm_matches = True
                        break
            if norm_matches:
                existing = [a.lower() for a in c.get('aliases', [])]
                if t_lower not in existing:
                    c.setdefault('aliases', []).append(t)
                    normalized_alias_additions += 1
                break

    if normalized_alias_additions:
        print(f"  Aliases added (normalization matches): {normalized_alias_additions}")
        alias_additions += normalized_alias_additions

    # 7. Generate new concepts for novel tags
    print(f"\n[7] Generating new concepts for {len(novel_tags)} novel tags...")
    new_concepts = []
    new_philosophy_entries = {}

    for t in sorted(novel_tags):
        if re.match(r'^[\$0-9b\.]+$', t):
            continue
        if len(t) < 3:
            continue

        pillar = auto_detect_pillar(t, tag_pillar_counts)
        new_c = generate_new_concept(t, pillar, tag_frequency.get(t, 1))

        base_id = new_c['id']
        if base_id in existing_ids or base_id in [nc['id'] for nc in new_concepts]:
            suffix = 1
            while (f"{base_id}-{suffix}" in existing_ids or
                   f"{base_id}-{suffix}" in [nc['id'] for nc in new_concepts]):
                suffix += 1
            new_c['id'] = f"{base_id}-{suffix}"

        new_cid = new_c['id']
        new_concepts.append(new_c)
        existing_ids.add(new_cid)

        new_philosophy_entries[new_cid] = {
            "philosophical_lineage": [],
            "epistemic_status": "instrumental",
            "normative_basis": "",
            "ontological_commitment": "",
            "temporal_ontology": "",
            "uncertainty_class": "",
            "governance_model": "",
            "semantic_contract_type": "",
            "philosophical_sources": [],
            "cross_pillar_analogs": [],
        }

        print(f"    NEW: {new_cid:40s} (pillar={pillar})")

    # 8. Fix conflicting aliases
    print("\n[8] Fixing conflicting aliases...")
    removed_aliases = fix_conflicting_aliases(concepts, all_item_tag_lists)
    print(f"  Removed overlapping aliases: {removed_aliases}")

    # Verify no conflicts remain
    alias_verify = defaultdict(list)
    for c in concepts:
        for a in c.get('aliases', []):
            alias_verify[a.lower()].append(c['id'])
    remaining = {a: cids for a, cids in alias_verify.items() if len(cids) > 1}
    if remaining:
        print(f"  WARNING: {len(remaining)} unresolved conflicts remain:")
        for a, cids in sorted(remaining.items()):
            print(f"    {a!r}: {cids}")
    else:
        print("  All alias conflicts resolved!")

    # 9. Add new concepts
    concepts[:0] = new_concepts

    # 10. Update philosophy_metadata
    print(f"\n[9] Updating philosophy_metadata.json with {len(new_philosophy_entries)} new entries...")
    philosophy.update(new_philosophy_entries)

    # 11. Save
    print("\n[10] Saving updated files...")
    save_json(ONTOLOGY_PATH, ontology)
    save_json(PHILOSOPHY_PATH, philosophy)

    # 12. Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Existing concepts before: {len(concepts) - len(new_concepts)}")
    print(f"  New concepts created:     {len(new_concepts)}")
    print(f"  Total concepts now:       {len(concepts)}")
    print(f"  Tags mapped to existing:  {len(mapped_tags)}")
    print(f"  New aliases added:        {alias_additions}")
    print(f"  Conflicting aliases removed: {removed_aliases}")
    print(f"  Philosophy metadata entries: {len(philosophy)}")
    print("=" * 60)

    # Final orphan verification — use the same matching function as the rest
    updated_concept_by_id, _, updated_labels_aliases = build_concept_lookup(concepts)
    final_unhandled = []
    for t in sorted(all_tags_set):
        t_lower = t.lower()
        if t_lower in KNOWN_SYNONYMS or t in KNOWN_SYNONYMS:
            continue
        matched = False
        for c in concepts:
            if tag_matches_concept(t, c['id'], c, updated_labels_aliases):
                matched = True
                break
        if not matched:
            final_unhandled.append(t)

    print(f"\n  Truly unhandled tags (pure noise / too generic): {len(final_unhandled)}")
    if final_unhandled:
        for t in sorted(final_unhandled):
            print(f"    {t}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
