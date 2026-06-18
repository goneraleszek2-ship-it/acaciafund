# AcaciaFund Pipeline

This repository contains the Palantir Foundry transforms for AcaciaFund.

## Project Structure

```
transforms-python/
├── src/
│   └── myproject/
│       ├── __init__.py
│       ├── pipeline.py
│       └── datasets/
│           ├── __init__.py
│           ├── ingestion.py      # Article ingestion from multiple sources
│           ├── scoring.py        # 6-dimension quality scoring
│           ├── analysis.py       # Trend detection and adoption patterns
│           ├── ontology.py       # Concept extraction and relationships
│           ├── export.py         # Static site data exports
│           └── processing.py     # Data processing and enrichment
```

## Transforms

### 1. Ingestion (`ingestion.py`)
- Collects articles from multiple sources (arXiv, PubMed, Semantic Scholar, GitHub, HackerNews)
- Outputs: `acacia_portal_clean_data`, `source_metadata`

### 2. Scoring (`scoring.py`)
- Computes 6-dimension quality scores:
  - Source Credibility (25%)
  - Technical Accuracy (25%)
  - Practical Value (20%)
  - Freshness (15%)
  - Trend Relevance (10%)
  - Educational Quality (5%)
- Outputs: `quality_scores`, `source_verification`

### 3. Analysis (`analysis.py`)
- Detects emerging trends and technology adoption patterns
- Outputs: `trend_analysis`, `technology_radar`

### 4. Ontology (`ontology.py`)
- Extracts concepts from articles
- Builds concept relationships (co-occurrences)
- Outputs: `ontology_concepts`, `ontology_relationships`

### 5. Export (`export.py`)
- Generates static outputs for website consumption
- Outputs: `export_quality_metrics`, `export_technology_radar`, `export_source_synthesis`

### 6. Processing (`processing.py`)
- Processes and enriches data for static site
- Generates content clusters and learning paths
- Outputs: `processed_data`, `content_clusters`, `learning_paths`

## Datasets

### Input
- `SOURCE_DATASET_PATH`: `/TierPalan-95733d/Acacia/SOURCE_DATASET_PATH`

### Output
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/acacia_portal_clean_data`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/source_metadata`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/quality_scores`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/source_verification`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/trend_analysis`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/technology_radar`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/ontology_concepts`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/ontology_relationships`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/export_quality_metrics`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/export_technology_radar`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/export_source_synthesis`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/processed_data`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/content_clusters`
- `/TierPalan-95733d/Acacia/acaciafund-pipeline/learning_paths`

## Dependencies

- `transforms`
- `transforms-expectations`
- `transforms-preview`
- `transforms-verbs`
- `foundry-transforms-lib-python`
- `polars`

## Development

```bash
# Run local tests
cd transforms-python
python -m pytest

# Build the package
python setup.py sdist bdist_wheel
```

## Deployment

The transforms are automatically deployed to Foundry when pushed to the main branch.

## Repository Information

- **RID**: `ri.stemma.main.repository.5f0e7650-f235-445e-a422-f1977854d32c`
- **Project Path**: `/TierPalan-95733d/Acacia/`
- **GitHub**: https://github.com/goneraleszek2-ship-it/acaciafund
