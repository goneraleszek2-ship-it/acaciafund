# Pillar System

AcaciaFund organizes all content into **three pillars**. Each pillar has an internal key, a URL segment, and 14 subcategories for content classification.

## Pillar Mapping

| Internal Key | URL Segment | Display Label | Items |
|---|---|---|---|
| `aml` | `compliance` | Compliance | ~92 |
| `stock` | `markets` | Markets | ~61 |
| `data-engineering` | `data` | Data Engineering | ~107 |

**Single source of truth:** `config.py:PILLAR_URL_MAP`

```python
PILLAR_URL_MAP = {"aml": "compliance", "stock": "markets", "data-engineering": "data"}
PILLAR_URL_REVERSE = {v: k for k, v in PILLAR_URL_MAP.items()}
```

## URL Hierarchy

```
/{pillar_url}/research/{topic}     # Research articles
/{pillar_url}/learn/{topic}        # Learn modules
/{pillar_url}/knowledge/{topic}    # Knowledge base
/{pillar_url}/glossary             # Auto-generated glossary
/knowledge/{platform-page}         # Cross-pillar platform pages
/search/?q=query                   # Client-side search
/admin/*.html                      # Admin dashboard
/graph/                            # Knowledge graph
```

## Pillar Subcategories

Each pillar has 14 subcategories defined in `config.py:PILLAR_SUBCATEGORIES`. These are used for content classification, ontology concept categorization, and knowledge taxonomy resolution.

### Compliance (`aml`)

| Key | Label | Icon |
|-----|-------|------|
| `risk-assessment` | Risk Assessment | ⚖️ |
| `cdd-kyc` | CDD/KYC | 🆔 |
| `sar-str` | SAR/STR Reporting | 🚨 |
| `regtech` | RegTech | 💻 |
| `sanctions` | Sanctions | 🚫 |
| `transaction-monitoring` | Transaction Monitoring | 📡 |
| `beneficial-ownership` | Beneficial Ownership | 🏢 |
| `trade-based-ml` | Trade-Based ML | 🚢 |
| `regulations` | Regulations | 📋 |
| `financial-intelligence` | Financial Intelligence | 🔍 |
| `crypto-aml` | Crypto AML | ₿ |
| `adverse-media` | Adverse Media | 📰 |
| `network-analysis` | Network Analysis | 🕸️ |
| `enforcement` | Enforcement | 🔨 |

### Data Engineering (`data-engineering`)

| Key | Label | Icon |
|-----|-------|------|
| `pipeline-architecture` | Pipeline Architecture | 🏗️ |
| `streaming` | Streaming | ⚡ |
| `batch-processing` | Batch Processing | 📦 |
| `storage-formats` | Storage Formats | 🗄️ |
| `data-quality` | Data Quality | ✅ |
| `data-governance` | Data Governance | 📜 |
| `analytics-engineering` | Analytics Engineering | 🧮 |
| `orchestration` | Orchestration | 🎛️ |
| `schema-management` | Schema Management | 📐 |
| `cost-optimization` | Cost Optimization | 💰 |
| `data-mesh-fabric` | Data Mesh/Fabric | 🌐 |
| `ml-pipelines` | ML Pipelines | 🤖 |
| `platform-engineering` | Platform Engineering | ⚙️ |
| `cybernetic-theory` | Cybernetic Theory | 🧠 |

### Markets (`stock`)

| Key | Label | Icon |
|-----|-------|------|
| `market-microstructure` | Market Microstructure | 🔬 |
| `volatility-analysis` | Volatility Analysis | 📊 |
| `quantitative-methods` | Quantitative Methods | 🧮 |
| `trading-strategies` | Trading Strategies | 🎯 |
| `risk-management` | Risk Management | 🛡️ |
| `portfolio-construction` | Portfolio Construction | 📐 |
| `industry-analysis` | Industry Analysis | 🏭 |
| `macro-economics` | Macro Economics | 🌍 |
| `earnings-analysis` | Earnings Analysis | 💹 |
| `commodity-markets` | Commodity Markets | 🛢️ |
| `semiconductor-sector` | Semiconductor Sector | 💎 |
| `behavioral-finance` | Behavioral Finance | 🧠 |
| `technical-analysis` | Technical Analysis | 📈 |
| `structured-products` | Structured Products | 🔗 |

## Knowledge-to-Pillar Mapping

11 **knowledge categories** are cross-pillar and resolved to pillar-specific subcategories via `config.py:KNOWLEDGE_TO_PILLAR_CATEGORY`:

| Category | Compliance | Markets | Data |
|----------|-----------|---------|------|
| `platform` | regtech | market-microstructure | platform-engineering |
| `guide` | cdd-kyc | trading-strategies | pipeline-architecture |
| `reference` | regulations | market-microstructure | data-governance |
| `architecture` | network-analysis | portfolio-construction | data-mesh-fabric |
| `foundations` | risk-assessment | market-microstructure | pipeline-architecture |
| `advanced-techniques` | network-analysis | quantitative-methods | streaming |
| `best-practices` | regtech | risk-management | data-quality |
| `regulations` | regulations | risk-management | data-governance |
| `industry-analysis` | trade-based-ml | industry-analysis | analytics-engineering |
| `market-analysis` | financial-intelligence | market-microstructure | analytics-engineering |
| `strategies` | regtech | trading-strategies | orchestration |

> **See also:** [Content Model](content-model.md) for the content data schema, [Knowledge Taxonomy](../03-content-system/knowledge-taxonomy.md) for detailed category definitions.
