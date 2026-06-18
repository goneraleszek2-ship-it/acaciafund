# AcaciaFund Pipeline - Foundry Transforms

## Overview

This repository contains Palantir Foundry transforms for AcaciaFund - a research synthesis and learning platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Foundry Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│  Input: SOURCE_DATASET_PATH                                 │
│  Output: acaciafund-pipeline/                               │
├─────────────────────────────────────────────────────────────┤
│  1. Ingestion → acacia_portal_clean_data                    │
│  2. Scoring → quality_scores, source_verification           │
│  3. Analysis → trend_analysis, technology_radar             │
│  4. Ontology → ontology_concepts, ontology_relationships    │
│  5. Export → quality_metrics, technology_radar, synthesis   │
│  6. Processing → processed_data, clusters, learning_paths   │
└─────────────────────────────────────────────────────────────┘
```

## 6-Day Scaling Plan

### Day 1: Foundry Infrastructure & Ingestion
- Provision Spark cluster (8 cores, 32GB RAM)
- Deploy 8 parallel ingestion agents
- Scale to 1,000 articles

### Day 2: ML-Powered Analysis
- Deploy ML classification models (Bloom, domain, content type)
- Implement distributed trend detection
- Scale to 3,000 articles

### Day 3: Ontology Expansion
- Expand ontology to 10,000 concepts
- Build knowledge graph with 50,000 relationships
- Scale to 5,000 articles

### Day 4: Image Generation
- Deploy 16 image generation agents
- Generate 50,000 section images
- Scale to 7,500 articles

### Day 5: Orchestration & QA
- Deploy Foundry Workflows
- Implement quality assurance pipeline
- Scale to 9,000 articles

### Day 6: Export & Deployment
- Export final data to static site
- Deploy to Cloudflare Pages
- Scale to 10,000 articles

## Resources

- **Total Cost**: $1,625 for 6 days
- **Compute**: Spark clusters (8-32 cores, 32-128GB RAM)
- **Agents**: 8-16 parallel agents per day
- **Storage**: 250TB distributed datasets

## Success Metrics

- ✅ 10,000 articles (103× increase)
- ✅ 250,000+ synthesis records
- ✅ 50,000 section images
- ✅ 92% time savings (17 hours vs. 204 manual)
- ✅ Image relevance ≥70%
- ✅ 100% alt-text coverage
