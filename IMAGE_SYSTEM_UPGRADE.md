# Image Matching System Upgrade

## Summary

Comprehensive upgrade to the AcaciaFund image matching system with:
- **90+ new icons** (41 abstract + 58 brand keywords)
- **Enhanced admin panel** with search, filtering, batch operations
- **Quality scoring system** (0-100 scale)
- **Image grouping** by topic, pillar, and quality tier
- **Better matching** with expanded icon library

---

## Changes Made

### 1. Expanded Icon Library (`core/visuals.py`)

#### New Abstract Icons (41)
**Data Formats:**
- parquet, avro, orc, iceberg, hudi

**ML/AI Frameworks:**
- scikit, mlflow

**Cloud Providers:**
- aws, gcp, azure

**Security:**
- encryption, zero-trust, iam

**Analytics:**
- dashboard, visualization, chart

**Data Operations:**
- etl, orchestration, dag

**Monitoring:**
- observability, monitoring, alerts, metrics

**Data Quality:**
- testing, validation, schema, lineage

**Automation:**
- ci-cd, automation, deployment

**Databases:**
- postgresql, mongodb, redis, elasticsearch

**AML:**
- risk, sanctions, pep, kyc

**Markets:**
- fintech, payments, neobank, wealth, robo

#### New Brand Keywords (58)
**Data Engineering:**
- dagster, prefect, kestra, apachebeam, databricks, confluent
- milvus, qdrant, pgvector, weaviate, pinecone, chromadb
- langchain, huggingface, vectordb, featurestore, dbtcloud

**ML/AI:**
- scikit, wandb, comet, neptune

**Security:**
- hashicorp, okta, auth0, keycloak

**Cloud DevOps:**
- bitbucket, circleci, argocd, flux, istio, linkerd, consul, nomad, vault

**Databases:**
- supabase, neon, planetscale, cockroachdb, timescale, influxdb, prometheus
- grafana, datadog, newrelic, sentry

**Analytics BI:**
- tableau, powerbi, looker, qlik

**Science:**
- biopython, rdkit

**Tools:**
- vscode, intellij

### 2. Enhanced Admin Panel (`app/admin_enhanced.py`)

#### Features
- **Dashboard** with stats (total articles, images, quality tiers)
- **Search & Filter:**
  - Text search across filenames and titles
  - Filter by pillar (AML, Stock, DE, Knowledge, Learn)
  - Filter by quality tier (high/medium/low)
- **Quality Scoring:**
  - Automatic 0-100 score per image
  - Breakdown: relevance (40%), resolution (25%), completeness (20%), visual (15%)
  - Tier classification: high (80-100), medium (50-79), low (0-49)
- **Batch Operations:**
  - Fetch images for multiple articles
  - Clear images for multiple articles
- **Image Management:**
  - Set/clear featured images
  - Set/clear section images
  - Tag images
- **Authentication:**
  - Simple session-based auth
  - 30-minute session timeout

#### Usage
```bash
pip install flask
python app/admin_enhanced.py
# Open http://localhost:5555/admin
```

### 3. Quality Scoring System

**Scoring Components:**
1. **Relevance (40%)**: From image metadata relevance_score
2. **Resolution (25%)**: Based on image dimensions
   - 1920x1080+: 100
   - 1200x600+: 80
   - 800x400+: 60
   - 600x300+: 40
   - <600x300: 20
3. **Completeness (20%)**: Metadata field presence
   - source, title, description, copyright, license, url
4. **Visual (15%)**: File size and format
   - WebP/AVIF: +15
   - JPEG: +10
   - File size >500KB: +20

**Quality Tiers:**
- **High (80-100)**: Excellent quality, suitable for production
- **Medium (50-79)**: Good quality, acceptable for use
- **Low (0-49)**: Poor quality, needs replacement

### 4. Image Grouping

Images are grouped by:
- **Content Type**: blog, learn, knowledge
- **Pillar**: aml, stock, data-engineering
- **Difficulty**: beginner, intermediate, advanced
- **Role**: featured, section_image
- **Quality Tier**: high, medium, low

---

## API Endpoints

### Images API
```
GET /api/images?q=search&pillar=aml&quality_tier=high
GET /api/images/<path>
GET /api/images/<path>/tags
POST /api/images/<path>/tags
DELETE /api/images/<path>/tags
```

### Article Images API
```
GET /api/articles/<slug>/images
POST /api/articles/<slug>/images
  - action: set_featured, clear_featured, set_section, clear_section
```

### Batch Operations
```
POST /api/batch/fetch-images
  - body: {article_ids: ["id1", "id2"]}
POST /api/batch/clear-images
  - body: {article_ids: ["id1", "id2"]}
```

### Authentication
```
POST /login
  - body: {username: "admin", password: "password"}
GET /logout
```

---

## File Structure

```
acaciafund/
├── core/visuals.py              # Enhanced with 90+ icons
├── app/
│   ├── admin.py                 # Original admin panel
│   └── admin_enhanced.py        # Enhanced admin panel
├── templates/
│   └── admin/
│       ├── index.html           # Dashboard template
│       └── login.html           # Login template
├── scripts/
│   ├── fetch_images.py          # Image fetching script
│   └── enhance_icons.py         # Icon enhancement script
└── IMAGE_SYSTEM_UPGRADE.md      # This file
```

---

## Next Steps

1. **Test Admin Panel**
   ```bash
   python app/admin_enhanced.py
   ```

2. **Rebuild Site**
   ```bash
   python build.py
   ```

3. **Deploy**
   ```bash
   bash deploy.sh
   ```

4. **Monitor Quality Scores**
   - Check `/registry/image-quality.json`
   - Review low-quality images in admin panel

---

## Notes

- Quality scores are saved to `/registry/image-quality.json`
- Image tags are saved to `/registry/image-tags.json`
- Session timeout: 30 minutes
- All changes are backward compatible with existing image system

---

## Credits

- Icons designed for AcaciaFund
- Based on existing visual system architecture
- Quality scoring inspired by image quality best practices
