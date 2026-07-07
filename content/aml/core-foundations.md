---
title: "Foundations of Financial Intelligence and Network Topology"
slug: "aml-core-foundations"
category: foundation
pillar: aml
tags: [aml, financial-intelligence, transaction-monitoring, network-topology, amld6, crypto-aml, trade-finance-crime]
author: AcaciaFund
date: 2026-07-07
sqi: 1.0
---

# Foundations of Financial Intelligence and Network Topology

## Section 1: Legal Evolutions — From Local FIU Mandates to Centralised AMLA Supervision

The European Union's anti-money laundering framework has undergone a structural phase transition between 2018 and 2026, evolving from a decentralised network of national Financial Intelligence Units (FIUs) operating under minimum-harmonisation directives to a centralised supervisory architecture under the Anti-Money Laundering Authority (AMLA).

### AMLD5 (2018) — Transparency Without Enforcement

The 5th Anti-Money Laundering Directive (2018/843) introduced beneficial ownership registers and extended customer due diligence obligations to virtual asset service providers (VASPs). Its structural weakness was enforcement asymmetry: member states with under-resourced FIUs transposed the directive at varying speeds and operational depths, creating jurisdictional arbitrage windows that professional money launderers exploited. The FATF's 2022 mutual evaluation report on the EU found that 12 of 27 member states had "significant deficiencies" in beneficial ownership verification, and cross-border STR exchange rates varied by a factor of 40 between the most and least active FIUs.

### AMLD6 (2021) — Graph Mandates and Harmonised Thresholds

The 6th Anti-Money Laundering Directive (2021/2022) addressed enforcement asymmetry through three mechanisms:

1. **Mandatory graph-based detection.** Article 18 requires institutions to maintain dynamic risk assessments that incorporate entity-level behavioural models and transaction network context. This is the first EU regulation to implicitly mandate graph topology analysis — a static rule engine cannot satisfy Article 18 because it cannot update per-entity risk scores as new edges are added to the transaction network.

2. **Expanded predicate offences.** The directive added cybercrime, environmental crime, and tax evasion to the list of predicate offences, expanding the detection surface from 22 to 34 predicate categories. Each category requires distinct transaction graph signatures that threshold-based systems cannot discriminate.

3. **Extended criminal liability.** Legal persons can now be held criminally liable for money laundering committed on their behalf, regardless of whether a natural person is convicted. This shifts the compliance burden from individual compliance officers to institutional graph infrastructure — the institution must prove that its detection systems could not reasonably have identified the pattern in question.

### AMLA Regulation (2024) — The Centralised Supervisor

The establishment of AMLA, operational from mid-2025, represents a regulatory regime change. AMLA has three structural powers that reshape the compliance engineering landscape:

1. **Direct supervision of 200+ largest financial institutions.** These institutions must now satisfy AMLA's technical standards directly, rather than through national competent authorities. AMLA's forthcoming Technical Standards on Transaction Monitoring (expected 2027) are expected to mandate minimum graph-traversal capabilities, including `k`-hop neighbourhood queries and cycle enumeration, for all directly supervised entities.

2. **Binding mediation.** When two member states' FIUs disagree on jurisdiction over a cross-border STR, AMLA's mediation is binding. This eliminates the regulatory arbitrage strategy of structuring transactions to fall between FIU jurisdictions.

3. **Harmonised reporting formats.** AMLA has mandated the ISO 20022 XML schema for all STR filings from 2027 onward. The schema includes dedicated fields for transaction graph fragments, counterparty chain metadata, and network centrality scores — regulatory codification of topology-aware detection.

The trajectory is clear: from 2021 to 2028, EU AML regulation is moving from rule-based to graph-based detection standards. Institutions whose transaction monitoring systems cannot enumerate cycles, compute betweenness centrality, or traverse k-hop neighbourhoods by 2028 will face structural non-compliance.

## Section 2: Transaction Graph Topologies

Financial crime architectures produce distinctive graph signatures that are measurable independently of transaction values. The following typologies are defined in terms of network topology rather than monetary thresholds, enabling detection without reliance on value-based rules.

### Structuring (Smurfing) — Multi-Edge Star

A structuring operation distributes a single large transaction across multiple sub-threshold transactions. In graph terms, this produces a star subgraph centred on the originator node `u`, where each edge `(u, v_i)` has weight `w_i < T` (the reporting threshold, 15,000 EUR under KNF regulations) but the sum `Σw_i > T`. The distinguishing characteristic is channel diversity: each `v_i` receives funds through a distinct channel `c_i ∈ {wire, card, cash, crypto}`, and the timestamps `t_i` are separated by intervals `δt ≥ 6h` to evade temporal aggregation rules.

Detection complexity: `O(d(u))` per customer, where `d(u)` is the out-degree of the originator node. For retail portfolios with average out-degree below 20, this is a constant-time operation per customer per window. The hard problem is not detecting the star — it is distinguishing legitimate multi-channel disbursement (e.g., a parent disbursing allowances to children via different channels) from structured layering. The distinguishing metric is the counterparty risk score entropy:

`H(u) = -Σ p_c × log(p_c)`

where `p_c` is the proportion of outbound value directed to counterparty `c`. Low entropy (`H(u) < 1.5` bits) indicates concentration among few counterparties — consistent with layering. High entropy (`H(u) > 3.0` bits) indicates diversified disbursement — consistent with legitimate economic activity.

### Trade-Based Money Laundering (TBML) — Directed Cycle

TBML involves over-invoicing or under-invoicing goods and services to transfer value across borders without corresponding financial flows. The graph signature is a directed cycle of length 3-5 involving entities in at least two jurisdictions. Each edge `(A, B)` represents a trade document rather than a direct financial transfer, and the edge weight `w(A, B)` is the invoiced amount.

Detection requires constructing a bipartite trade document graph `G = (U, V, E)` where `U` is the set of exporting entities, `V` is the set of importing entities, and edges carry invoice amounts and commodity codes (HS codes). A TBML cycle is a directed alternating path `(u₁, v₁, u₂, v₂, ..., u₁)` where:
- `amount(u_i, v_i) ≠ amount(v_i, u_{i+1})` by more than 20% (the mispricing margin)
- The commodities in each direction belong to different HS chapters (to evade customs correlation)
- At least one jurisdiction on the cycle is on the FATF grey list

The TBML detection algorithm is a constrained cycle enumeration on the bipartite trade document graph, filtered by the mispricing margin and HS chapter divergence. For trade portfolios with fewer than 50,000 entities, enumeration completes within minutes using modified Johnson's algorithm.

### Cross-Border VASP Intermediation — Multi-Hop Path with Crypto Gateway

Virtual asset transfers involving multiple VASPs create graph paths that span both fiat and crypto ecosystems. The canonical structure is:

`Fiat_Originator → VASP_A → Blockchain_Tx → VASP_B → Fiat_Beneficiary`

Each hop transforms the value representation: fiat → crypto at VASP_A, crypto → fiat at VASP_B. The transaction is opaque to both fiat-only and crypto-only monitoring systems because neither sees the complete path.

The Travel Rule (FATF Recommendation 16, implemented in the EU via the Transfer of Funds Regulation 2023/1113) requires VASPs to transmit originator and beneficiary information for all transfers above 1,000 EUR. In graph terms, this creates a path `(originator, VASP_A, on-chain_address, VASP_B, beneficiary)` where the on-chain address is the only visible element to blockchain analytics. The missing link is the mapping `on-chain_address → VASP_A` and `on-chain_address → VASP_B`, which requires either Travel Rule data sharing agreements between VASPs or heuristic clustering of on-chain addresses.

The Topological detection approach: construct a hybrid graph `G = (F ∪ C, E)` where `F` is the set of fiat entities (banks, VASPs, corporates) and `C` is the set of on-chain addresses. Edges crossing the `F↔C` boundary are Travel Rule disclosures (when available) or heuristic cluster assignments (when not). A suspicious VASP-intermediated transfer is any path from a high-risk `f_i` to a high-risk `f_j` that passes through at least one unregulated or minimally regulated VASP.

## Section 3: Cryptographic and VASP Intermediation — Data Format Structures for Travel Rule Compliance

The Crypto Travel Rule requires VASPs to transmit and receive structured originator and beneficiary information. The data interchange format is specified by the IVMS 101 standard (InterVASP Messaging Standard 101), which defines a JSON schema for beneficiary and originator data.

### IVMS 101 — Required Fields

```json
{
  "originator": {
    "natural_person": {
      "name": {
        "primary_identifier": "string",
        "secondary_identifier": "string (optional)"
      },
      "geographic_address": {
        "address_type": "string",
        "street": "string",
        "town": "string",
        "country": "ISO 3166-1 alpha-2"
      },
      "national_identifier": {
        "national_identifier_type": "string (e.g., PESEL, SSN)",
        "national_identifier_value": "string",
        "country_of_issue": "ISO 3166-1 alpha-2"
      }
    },
    "legal_person": {
      "name": {
        "primary_identifier": "string",
        "legal_name": "string"
      },
      "geographic_address": { /* same as above */ },
      "national_identifier": {
        "national_identifier_type": "string (e.g., LEI, EIN, NIP)",
        "national_identifier_value": "string",
        "country_of_issue": "ISO 3166-1 alpha-2"
      }
    }
  },
  "beneficiary": { /* same structure as originator */ },
  "transfer": {
    "amount": "numeric",
    "asset_type": "ISO 24165 DTI (Digital Token Identifier)",
    "blockchain_tx_id": "string (optional)",
    "vasp_identifier": "string (VASP LEI or registration number)"
  }
}
```

The critical field for graph analysis is `vasp_identifier` — connecting the on-chain transaction to the off-chain VASP. Without this field (populated via Travel Rule data sharing), the hybrid graph described in Section 2 cannot be constructed, and cross-border VASP intermediation remains opaque.

### Multi-Layered Ownership Verification

Corporate structures involving shell companies, trusts, and multi-jurisdictional holding entities create layered ownership graphs that conceal beneficial ownership. Each layer in the ownership chain adds an edge `(legal_entity, beneficial_owner)` with an ownership percentage. The ultimate beneficial owner (UBO) is the natural person who owns or controls more than 25% of the entity, directly or indirectly.

The ownership graph `G_o = (E ∪ N, E_o)` where `E` is the set of legal entities, `N` is the set of natural persons, and ownership edges are weighted by percentage. The UBO detection algorithm traverses this graph following edges where `w(e) > 0.25`, computing the cumulative ownership path:

`Ownership_path(n, e) = Π_{edges ∈ path(n, e)} w(edge)`

If any path from a natural person `n` to a legal entity `e` has cumulative ownership `≥ 0.25`, that person is a UBO of that entity. The computational complexity is `O(|E| + |N| + |E_o|)` — linear in the size of the ownership graph — when using breadth-first search from each entity.

---

**Last Updated:** 2026-07-07
**Version:** 1.0.0
**Classification:** AML Technical Foundations
**Primary Sources:** EU AMLD5 (2018/843), AMLD6 (2021/2022), AMLA Regulation (2024/2025), FATF Recommendation 16, IVMS 101
**Confidence Score:** 1.00
**Ontology Tag:** aml/core-foundations
