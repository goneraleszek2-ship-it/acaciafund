# Glossary Generation

Per-pillar glossary pages are auto-generated from ontology concepts by `scripts/generate_glossaries.py`.

## How It Works

The glossary generator:
1. Loads ontology concepts from `data/ontology.json`
2. Groups concepts by pillar (`aml`, `stock`, `data-engineering`)
3. For each pillar, generates a glossary page listing all concepts in that pillar
4. Writes glossary entries to `registry.json` as knowledge-type content
5. Glossary pages appear at `/{pillar_url}/glossary/`

## Glossary Entry Format

Each glossary entry in `registry.json`:

```json
{
  "slug": "aml/knowledge/glossary",
  "title": "Compliance Glossary",
  "content_type": "knowledge",
  "pillar": "aml",
  "category": "reference",
  "body_html": "<dl><dt>KYC</dt><dd>Know Your Customer...</dd>...</dl>",
  ...
}
```

## What Gets Included

- All ontology concepts for the pillar (16 per pillar, 48 total)
- Each concept shows: label, definition, aliases, confidence score
- Concepts are grouped by category (risk-assessment, cdd-kyc, etc.)
- Links to related concepts within the same pillar

## Running the Generator

```bash
python3 scripts/generate_glossaries.py
```

Requires `data/ontology.json` to exist. If ontology doesn't exist yet:
```bash
python3 -c "
from core.ontology import OntologyManager
m = OntologyManager()
m.seed_all_pillars()
m.seed_relations()
m.save('data/ontology.json')
"
```

## Interaction with Ontology

Glossary generation depends on the ontology:
- **After adding concepts:** Run `generate_glossaries.py` to update glossary pages
- **After modifying concepts:** Re-run to reflect changes
- **If concepts are deleted:** Glossary entries are updated (orphaned entries removed)

> **See also:** [Ontology Model](../04-ontology-knowledge-graph/ontology-model.md), [CLI Commands](../reference/cli-commands.md)
