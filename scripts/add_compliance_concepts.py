#!/usr/bin/env python3
"""Add 2026 compliance landscape concepts to ontology and philosophy metadata.

Adds 14 new concepts spanning GDPR anonymization, synthetic data, debiasing,
AI Act, DORA, NIS2, MiCA, ESG double materiality, and data act interoperability.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"
PHILOSOPHY_PATH = PROJECT_ROOT / "data" / "philosophy_metadata.json"

def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# New concept definitions (basic + philosophical metadata)
# ---------------------------------------------------------------------------

NEW_CONCEPTS = [
    # 1. GDPR ANONYMIZATION (Data Engineering, best-practices)
    {
        "id": "gdpr-anonymization",
        "label": "GDPR Anonymization & Pseudonymization",
        "description": "Techniques and regulatory requirements for rendering personal data non-identifiable under GDPR Article 26 and Recital 26.",
        "pillar": "data-engineering",
        "category": "best-practices",
        "aliases": ["anonymization", "pseudonymization", "data masking", "de-identification"],
        "philosophical_lineage": ["privacy_philosophy", "contextual_integrity", "nissenbaum"],
        "epistemic_status": "regulatory",
        "normative_basis": "kantian_duty",
        "ontological_commitment": "constructivist",
        "temporal_ontology": "state_based",
        "uncertainty_class": "ambiguity",
        "governance_model": "hierarchical",
        "semantic_contract_type": "constitutive",
        "philosophical_sources": [
            "Nissenbaum, Helen. Privacy in Context: Technology, Policy, and the Integrity of Social Life (2009)",
            "Floridi, Luciano. The Ethics of Information (2013)",
            "European Parliament. GDPR Article 26 and Recital 26 (2016/679)"
        ],
        "cross_pillar_analogs": ["data-security", "cyber-aml"]
    },
    # 2. GDPR SYNTHETIC DATA (Data Engineering, advanced-techniques)
    {
        "id": "gdpr-synthetic-data",
        "label": "Synthetic Data Generation for GDPR Compliance",
        "description": "Generation of artificial datasets that preserve statistical properties of original data without exposing personal information.",
        "pillar": "data-engineering",
        "category": "advanced-techniques",
        "aliases": ["synthetic data", "data generation", "generative modeling", "synth data"],
        "philosophical_lineage": ["philosophy_of_simulation", "epistemic_trust", "fictionalism"],
        "epistemic_status": "constitutive",
        "normative_basis": "pragmatic",
        "ontological_commitment": "fictionalist",
        "temporal_ontology": "state_based",
        "uncertainty_class": "measurable",
        "governance_model": "algorithmic",
        "semantic_contract_type": "coordinating",
        "philosophical_sources": [
            "Baudrillard, Jean. Simulacra and Simulation (1981)",
            "Derman, Emanuel. Models. Behaving. Badly (2011)",
            "Goodfellow, Ian et al. Generative Adversarial Nets (2014)"
        ],
        "cross_pillar_analogs": ["transaction-monitoring", "market-microstructure"]
    },
    # 3. DEBIASING PIPELINE (Data Engineering, best-practices)
    {
        "id": "debiasing-pipeline",
        "label": "Debiasing Pipeline",
        "description": "Systematic processes for detecting and mitigating bias in ML training data, features, and model outputs.",
        "pillar": "data-engineering",
        "category": "best-practices",
        "aliases": ["bias mitigation", "fairness pipeline", "bias detection", "algorithmic fairness"],
        "philosophical_lineage": ["ethics_of_algorithm", "distributive_justice", "rawlsian"],
        "epistemic_status": "normative",
        "normative_basis": "rawlsian",
        "ontological_commitment": "constructivist",
        "temporal_ontology": "processual",
        "uncertainty_class": "ambiguity",
        "governance_model": "algorithmic",
        "semantic_contract_type": "constitutive",
        "philosophical_sources": [
            "Rawls, John. A Theory of Justice (1971) — Difference principle",
            "Crawford, Kate. Atlas of AI (2021)",
            "Noble, Safiya Umoja. Algorithms of Oppression (2018)"
        ],
        "cross_pillar_analogs": ["aml-program", "portfolio-optimization"]
    },
    # 4. DIFFERENTIAL PRIVACY (Data Engineering, advanced-techniques)
    {
        "id": "differential-privacy",
        "label": "Differential Privacy",
        "description": "Formal mathematical framework for quantifying and limiting privacy leakage in statistical queries and ML training.",
        "pillar": "data-engineering",
        "category": "advanced-techniques",
        "aliases": ["DP", "epsilon-delta privacy", "privacy budget", "noise injection"],
        "philosophical_lineage": ["privacy_philosophy", "epistemic_humility"],
        "epistemic_status": "constitutive",
        "normative_basis": "utilitarian",
        "ontological_commitment": "fictionalist",
        "temporal_ontology": "event_based",
        "uncertainty_class": "measurable",
        "governance_model": "algorithmic",
        "semantic_contract_type": "coordinating",
        "philosophical_sources": [
            "Dwork, Cynthia; Roth, Aaron. The Algorithmic Foundations of Differential Privacy (2014)",
            "Nissenbaum, Helen. Privacy in Context (2009)",
            "Floridi, Luciano. The Logic of Information (2019)"
        ],
        "cross_pillar_analogs": ["data-security", "cyber-aml"]
    },
    # 5. FEDERATED LEARNING (Data Engineering, advanced-techniques)
    {
        "id": "federated-learning",
        "label": "Federated Learning",
        "description": "Distributed ML paradigm where models are trained across decentralized data sources without raw data leaving its origin.",
        "pillar": "data-engineering",
        "category": "advanced-techniques",
        "aliases": ["federated ML", "distributed training", "privacy-preserving ML", "federated averaging"],
        "philosophical_lineage": ["distributed_epistemology", "data_sovereignty"],
        "epistemic_status": "constitutive",
        "normative_basis": "contractarian",
        "ontological_commitment": "pluralist",
        "temporal_ontology": "processual",
        "uncertainty_class": "knightian",
        "governance_model": "polycentric",
        "semantic_contract_type": "constitutive",
        "philosophical_sources": [
            "McMahan, Brendan et al. Communication-Efficient Learning of Deep Networks from Decentralized Data (2017)",
            "Ostrom, Elinor. Governing the Commons (1990)",
            "Floridi, Luciano. The Fourth Revolution (2014)"
        ],
        "cross_pillar_analogs": ["distributed-systems", "data-mesh"]
    },
    # 6. MODEL CARDS (Data Engineering, best-practices)
    {
        "id": "model-cards",
        "label": "Model Cards & Documentation Standards",
        "description": "Structured transparency reporting for ML models covering intended use, performance, limitations, and ethical considerations.",
        "pillar": "data-engineering",
        "category": "best-practices",
        "aliases": ["model card", "model documentation", "model transparency report", "model governance"],
        "philosophical_lineage": ["transparency_ethics", "documentation_philosophy"],
        "epistemic_status": "constitutive",
        "normative_basis": "kantian_duty",
        "ontological_commitment": "constructivist",
        "temporal_ontology": "state_based",
        "uncertainty_class": "ambiguity",
        "governance_model": "polycentric",
        "semantic_contract_type": "descriptive",
        "philosophical_sources": [
            "Mitchell, Margaret et al. Model Cards for Model Reporting (2019)",
            "Floridi, Luciano. The Ethics of Information (2013)",
            "Hildebrandt, Mireille. Law for Computer Scientists (2020)"
        ],
        "cross_pillar_analogs": ["regulatory-reporting", "data-contracts"]
    },
    # 7. FAIRNESS METRICS (Data Engineering, best-practices)
    {
        "id": "fairness-metrics",
        "label": "Fairness Metrics in ML",
        "description": "Quantitative measures for evaluating algorithmic fairness across demographic groups: demographic parity, equal opportunity, equalized odds.",
        "pillar": "data-engineering",
        "category": "best-practices",
        "aliases": ["algorithmic fairness", "demographic parity", "equal opportunity", "fairness metric"],
        "philosophical_lineage": ["distributive_justice", "rawlsian", "algorithmic_fairness"],
        "epistemic_status": "normative",
        "normative_basis": "rawlsian",
        "ontological_commitment": "constructivist",
        "temporal_ontology": "state_based",
        "uncertainty_class": "measurable",
        "governance_model": "algorithmic",
        "semantic_contract_type": "coordinating",
        "philosophical_sources": [
            "Dwork, Cynthia et al. Fairness Through Awareness (2012)",
            "Barocas, Solon; Selbst, Andrew. Big Data's Disparate Impact (2016)",
            "Rawls, John. A Theory of Justice (1971)"
        ],
        "cross_pillar_analogs": ["aml-program", "portfolio-optimization"]
    },
    # 8. AI ACT HIGH-RISK (Data Engineering, regulations — cross-pillar)
    {
        "id": "ai-act-high-risk",
        "label": "EU AI Act — High-Risk Classification",
        "description": "EU regulation categorizing AI systems by risk level, imposing conformity assessments, transparency, and human oversight for high-risk applications.",
        "pillar": "data-engineering",
        "category": "regulations",
        "aliases": ["AI Act", "high-risk AI", "EU AI Act", "AI risk classification"],
        "philosophical_lineage": ["regulatory_philosophy", "precautionary_principle", "sunstein"],
        "epistemic_status": "regulatory",
        "normative_basis": "kantian_duty",
        "ontological_commitment": "realist",
        "temporal_ontology": "state_based",
        "uncertainty_class": "ambiguity",
        "governance_model": "hierarchical",
        "semantic_contract_type": "constitutive",
        "philosophical_sources": [
            "European Commission. Proposal for AI Act (2021/0106/COD)",
            "Sunstein, Cass. Laws of Fear: Beyond the Precautionary Principle (2005)",
            "Floridi, Luciano. The Cambridge Handbook of Information Law (2020)"
        ],
        "cross_pillar_analogs": ["regtech", "transaction-monitoring", "high-frequency-trading"]
    },
    # 9. AI CONFORMITY ASSESSMENT (Data Engineering, regulations)
    {
        "id": "ai-conformity-assessment",
        "label": "AI Conformity Assessment & Auditing",
        "description": "Procedures for verifying AI system compliance with regulatory standards, including documentation, testing, and continuous monitoring.",
        "pillar": "data-engineering",
        "category": "regulations",
        "aliases": ["AI auditing", "conformity assessment", "AI compliance audit", "algorithm audit"],
        "philosophical_lineage": ["conformity_theory", "audit_philosophy"],
        "epistemic_status": "regulatory",
        "normative_basis": "pragmatic",
        "ontological_commitment": "realist",
        "temporal_ontology": "processual",
        "uncertainty_class": "measurable",
        "governance_model": "algorithmic",
        "semantic_contract_type": "descriptive",
        "philosophical_sources": [
            "Hildebrandt, Mireille. Law for Computer Scientists (2020)",
            "EU AI Act. Conformity Assessment Procedures (Title III, Chapter 3)",
            "Floridi, Luciano. The Ethics of Information (2013)"
        ],
        "cross_pillar_analogs": ["regtech", "ml-pipeline"]
    },
    # 10. DORA ICT RISK (Data Engineering, regulations — cross-pillar)
    {
        "id": "dora-ict-risk",
        "label": "DORA — ICT Risk Management",
        "description": "EU Digital Operational Resilience Act requirements for ICT risk management, incident reporting, digital resilience testing, and third-party risk.",
        "pillar": "data-engineering",
        "category": "regulations",
        "aliases": ["DORA", "Digital Operational Resilience Act", "ICT risk", "operational resilience"],
        "philosophical_lineage": ["resilience_philosophy", "systems_theory", "brittleness"],
        "epistemic_status": "regulatory",
        "normative_basis": "utilitarian",
        "ontological_commitment": "realist",
        "temporal_ontology": "processual",
        "uncertainty_class": "knightian",
        "governance_model": "hierarchical",
        "semantic_contract_type": "coordinating",
        "philosophical_sources": [
            "European Parliament. Regulation (EU) 2022/2554 (DORA)",
            "Taleb, Nassim Nicholas. Antifragile (2012)",
            "Perrow, Charles. Normal Accidents (1984)"
        ],
        "cross_pillar_analogs": ["aml-program", "data-observability", "distributed-systems"]
    },
    # 11. NIS2 CYBER RESILIENCE (Data Engineering, best-practices)
    {
        "id": "nis2-cyber-resilience",
        "label": "NIS2 Directive — Cybersecurity Resilience",
        "description": "EU Directive on measures for a high common level of cybersecurity across critical sectors, expanding scope and incident reporting obligations.",
        "pillar": "data-engineering",
        "category": "best-practices",
        "aliases": ["NIS2", "NIS 2 Directive", "cyber resilience", "network security"],
        "philosophical_lineage": ["cybersecurity_ethics", "operational_resilience"],
        "epistemic_status": "regulatory",
        "normative_basis": "kantian_duty",
        "ontological_commitment": "realist",
        "temporal_ontology": "processual",
        "uncertainty_class": "knightian",
        "governance_model": "hierarchical",
        "semantic_contract_type": "coordinating",
        "philosophical_sources": [
            "European Parliament. Directive (EU) 2022/2555 (NIS2)",
            "Schneier, Bruce. Click Here to Kill Everybody (2018)",
            "Sunstein, Cass. Laws of Fear (2005)"
        ],
        "cross_pillar_analogs": ["cyber-aml", "data-security", "dora-ict-risk"]
    },
    # 12. MiCA CRYPTO ASSETS (AML, regulations — cross-pillar with stock)
    {
        "id": "mica-crypto-assets",
        "label": "MiCA — Markets in Crypto-Assets Regulation",
        "description": "EU regulation establishing a harmonized framework for crypto-assets, stablecoins, and crypto-asset service providers (CASPs).",
        "pillar": "aml",
        "category": "crypto-aml",
        "aliases": ["MiCA", "Markets in Crypto-Assets", "crypto regulation", "CASPs"],
        "philosophical_lineage": ["monetary_philosophy", "sovereignty", "trust_in_code"],
        "epistemic_status": "regulatory",
        "normative_basis": "contractarian",
        "ontological_commitment": "realist",
        "temporal_ontology": "state_based",
        "uncertainty_class": "ambiguity",
        "governance_model": "hierarchical",
        "semantic_contract_type": "constitutive",
        "philosophical_sources": [
            "European Commission. Proposal for MiCA Regulation (2020/0265/COD)",
            "Pistor, Katharina. The Code of Capital (2019)",
            "Nakamoto, Satoshi. Bitcoin: A Peer-to-Peer Electronic Cash System (2008)"
        ],
        "cross_pillar_analogs": ["crypto-aml", "travel-rule"]
    },
    # 13. ESG DOUBLE MATERIALITY (Stock, industry-analysis)
    {
        "id": "esg-double-materiality",
        "label": "ESG Double Materiality",
        "description": "CSRD framework requiring companies to report both how sustainability issues affect their value (financial materiality) and how they affect the world (impact materiality).",
        "pillar": "stock",
        "category": "industry-analysis",
        "aliases": ["double materiality", "CSRD materiality", "impact materiality", "financial materiality"],
        "philosophical_lineage": ["stakeholder_theory", "intergenerational_justice"],
        "epistemic_status": "normative",
        "normative_basis": "rawlsian",
        "ontological_commitment": "pluralist",
        "temporal_ontology": "event_based",
        "uncertainty_class": "knightian",
        "governance_model": "polycentric",
        "semantic_contract_type": "constitutive",
        "philosophical_sources": [
            "European Commission. Corporate Sustainability Reporting Directive (2022/2464)",
            "Rawls, John. A Theory of Justice (1971) — Just savings principle",
            "Freeman, R. Edward. Strategic Management: A Stakeholder Approach (1984)"
        ],
        "cross_pillar_analogs": ["aml-program", "esg-investing"]
    },
    # 14. DATA ACT INTEROPERABILITY (Data Engineering, architecture)
    {
        "id": "data-act-interoperability",
        "label": "EU Data Act — Data Interoperability",
        "description": "EU regulation promoting fair access to and reuse of data, mandating interoperability standards, data portability, and smart contract safeguards.",
        "pillar": "data-engineering",
        "category": "architecture",
        "aliases": ["EU Data Act", "data interoperability", "data portability", "smart contract safeguards"],
        "philosophical_lineage": ["data_commons", "information_economics"],
        "epistemic_status": "regulatory",
        "normative_basis": "contractarian",
        "ontological_commitment": "realist",
        "temporal_ontology": "state_based",
        "uncertainty_class": "ambiguity",
        "governance_model": "polycentric",
        "semantic_contract_type": "coordinating",
        "philosophical_sources": [
            "European Commission. Data Act Regulation (2023/2854)",
            "Ostrom, Elinor. Governing the Commons (1990)",
            "Lessig, Lawrence. Code and Other Laws of Cyberspace (1999)"
        ],
        "cross_pillar_analogs": ["data-contracts", "schema-registry"]
    },
]

# ---------------------------------------------------------------------------
# New relations to add
# ---------------------------------------------------------------------------

NEW_RELATIONS = [
    # GDPR chain
    ("gdpr-anonymization", "gdpr-synthetic-data", "enables", "data-engineering"),
    ("gdpr-synthetic-data", "data-quality", "requires", "data-engineering"),
    ("gdpr-synthetic-data", "debiasing-pipeline", "enables", "data-engineering"),
    ("gdpr-anonymization", "data-security", "implements", "data-engineering"),
    ("differential-privacy", "gdpr-anonymization", "implements", "data-engineering"),
    ("federated-learning", "differential-privacy", "related_to", "data-engineering"),

    # Debiasing + Fairness chain
    ("debiasing-pipeline", "fairness-metrics", "requires", "data-engineering"),
    ("debiasing-pipeline", "ml-pipeline", "implements", "data-engineering"),
    ("model-cards", "ml-pipeline", "implements", "data-engineering"),
    ("model-cards", "debiasing-pipeline", "requires", "data-engineering"),

    # AI Act cross-pillar
    ("ai-act-high-risk", "transaction-monitoring", "regulates", "cross-pillar"),
    ("ai-act-high-risk", "high-frequency-trading", "regulates", "cross-pillar"),
    ("ai-act-high-risk", "ml-pipeline", "regulates", "cross-pillar"),
    ("ai-conformity-assessment", "ml-pipeline", "implements", "data-engineering"),
    ("ai-conformity-assessment", "model-cards", "requires", "data-engineering"),
    ("ai-conformity-assessment", "ai-act-high-risk", "implements", "cross-pillar"),

    # DORA resilience network
    ("dora-ict-risk", "data-observability", "requires", "cross-pillar"),
    ("dora-ict-risk", "distributed-systems", "requires", "cross-pillar"),
    ("dora-ict-risk", "data-contracts", "requires", "cross-pillar"),
    ("dora-ict-risk", "orchestration", "requires", "cross-pillar"),

    # NIS2
    ("nis2-cyber-resilience", "cyber-aml", "related_to", "cross-pillar"),
    ("nis2-cyber-resilience", "data-security", "regulates", "cross-pillar"),
    ("nis2-cyber-resilience", "dora-ict-risk", "related_to", "cross-pillar"),

    # MiCA
    ("mica-crypto-assets", "crypto-aml", "regulates", "cross-pillar"),
    ("mica-crypto-assets", "travel-rule", "regulates", "aml"),
    ("mica-crypto-assets", "transaction-monitoring", "regulates", "cross-pillar"),

    # ESG
    ("esg-double-materiality", "esg-investing", "regulates", "stock"),
    ("esg-double-materiality", "aml-program", "related_to", "cross-pillar"),

    # Data Act
    ("data-act-interoperability", "data-contracts", "requires", "data-engineering"),
    ("data-act-interoperability", "schema-registry", "requires", "data-engineering"),
    ("data-act-interoperability", "data-mesh", "related_to", "cross-pillar"),
]


def concept_exists(ontology: dict, cid: str) -> bool:
    return any(c.get("id") == cid for c in ontology.get("concepts", []))


def add_concepts_and_relations() -> int:
    ontology = load_json(ONTOLOGY_PATH)
    metadata = load_json(PHILOSOPHY_PATH)

    added = 0
    for newc in NEW_CONCEPTS:
        cid = newc["id"]
        if concept_exists(ontology, cid):
            print(f"  Concept '{cid}' already in ontology — skipping")
            continue
        # Build ontology entry (basic fields + philosophical fields)
        entry = {
            "id": newc["id"],
            "label": newc["label"],
            "description": newc.get("description", ""),
            "pillar": newc["pillar"],
            "category": newc["category"],
            "aliases": newc.get("aliases", []),
            "properties": {},
            "source_inspiration": "",
            "confidence_score": 1.0,
            "created_at": NOW,
            "updated_at": NOW,
        }
        # Add all philosophical fields (filled directly)
        PHILO_FIELDS = [
            "philosophical_lineage", "epistemic_status", "normative_basis",
            "ontological_commitment", "temporal_ontology", "uncertainty_class",
            "governance_model", "semantic_contract_type", "philosophical_sources",
            "cross_pillar_analogs",
        ]
        for f in PHILO_FIELDS:
            val = newc.get(f)
            if val is None:
                val = [] if f in ("philosophical_lineage", "philosophical_sources", "cross_pillar_analogs") else ""
            entry[f] = val

        ontology["concepts"].append(entry)

        # Add to philosophy metadata
        meta_entry = {}
        for f in PHILO_FIELDS:
            if f in newc:
                meta_entry[f] = newc[f]
        metadata[cid] = meta_entry

        print(f"  Added concept '{cid}' ({newc['label']})")
        added += 1

    # Add relations
    rel_added = 0
    existing_relations = set()
    for r in ontology.get("relations", []):
        existing_relations.add((r["source_id"], r["target_id"], r["relation_type"]))

    for src, tgt, rtype, pillar in NEW_RELATIONS:
        key = (src, tgt, rtype)
        if key in existing_relations:
            print(f"  Relation {src} --{rtype}--> {tgt} already exists — skipping")
            continue
        rel = {
            "source_id": src,
            "target_id": tgt,
            "relation_type": rtype,
            "strength": 1.0,
            "evidence": [],
            "pillar": pillar,
            "created_at": NOW,
        }
        ontology.setdefault("relations", []).append(rel)
        existing_relations.add(key)
        rel_added += 1

    # Save
    save_json(ONTOLOGY_PATH, ontology)
    save_json(PHILOSOPHY_PATH, metadata)
    print(f"\nAdded {added} concepts, {rel_added} relations to ontology + metadata")
    return added


def main():
    added = add_concepts_and_relations()
    total = added
    # Count
    ontology = load_json(ONTOLOGY_PATH)
    metadata = load_json(PHILOSOPHY_PATH)
    print(f"Ontology now has {len(ontology['concepts'])} concepts, {len(ontology.get('relations', []))} relations")
    print(f"Metadata now has {len(metadata)} entries")
    return 0 if added > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
