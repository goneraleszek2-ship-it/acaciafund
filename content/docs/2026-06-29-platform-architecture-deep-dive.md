---
title: Polish Electricity Balancing Market — PSE Data Specifications and Real-Time Pipeline Architecture
slug: docs/platform-architecture
category: knowledge
pillar: data-engineering
tags: [pse, rynek-bilansujacy, balancing-market, energy, data-pipeline, poland, res, real-time]
author: AcaciaFund
date: 2026-06-29
sqi: 0.93
---

# Polish Electricity Balancing Market — PSE Data Specifications and Real-Time Pipeline Architecture

The Polish electricity balancing market (Rynek Bilansujący — RB), operated by Polskie Sieci Elektroenergetyczne (PSE), is the mechanism through which generation and consumption are matched in real time after the day-ahead and intraday markets have settled. This document specifies the data products, ingestion contracts, and pipeline architecture required to consume PSE balancing market data for real-time analytics, regulatory reporting, and renewable energy source (RES) integration monitoring.

## Market Architecture

The RB operates on a 15-minute settlement period (okres bilansowania). Each day is divided into 96 settlement periods, starting at 00:00. Market participants — generators, suppliers, and balancing-responsible entities — submit their scheduled generation and consumption to PSE at gate closure, which occurs 60 minutes before the start of the settlement period.

### Imbalance Pricing Mechanism

PSE calculates two imbalance prices for each settlement period:

**Cena Rozliczeniowa Energii Bilansującej (CREB):** The marginal price for energy balancing. CREB is published for each settlement period approximately 30 minutes after the period closes. It reflects the marginal cost of the most expensive balancing energy activated in that period. If no balancing energy was activated, CREB equals the day-ahead reference price (Cena Rozliczeniowa Rynku Bilansującego — CRRB).

**Cena Rozliczeniowa Rynku Bilansującego (CRRB):** The volume-weighted average price of all balancing energy transactions in the settlement period. CRRB serves as the reference price for calculating imbalance charges.

The key regulatory distinction: negative imbalance (undergeneration) is priced at `max(CREB, CRRB)` and positive imbalance (overgeneration) is priced at `min(CREB, CRRB)`. This asymmetric pricing creates a structural incentive for accurate scheduling — a generator that deviates from its schedule pays a penalty proportional to the magnitude of the deviation multiplied by the imbalance price differential.

### RES Integration

The integration of renewable energy sources into the RB follows the dispatch priority principle (I102 of the Polish Energy Law). RES installations with installed capacity below 500 kW are not subject to imbalance charges and receive a fixed feed-in tariff. RES installations above 500 kW must participate fully in the balancing market, forecasting their generation and bearing imbalance costs.

For data pipelines consuming PSE data, the structural challenge of RES integration manifests as increasing volatility in the scheduled-vs-actual generation gap. For a 1 GW wind farm cluster in the Baltic Sea region, the mean absolute error of day-ahead generation forecasts is approximately 8% of installed capacity in summer and 14% in winter. This forecast error translates directly into balancing energy demand. When the forecast error exceeds 10% of national demand (approximately 2 GW for Poland's peak load of 25 GW), PSE activates its operational reserve procurement mechanism — the interventional balancing energy market.

## PSE Data Products — Machine-Readable Contract Specifications

PSE publishes operational data through the PSE S.A. Platforma Wymiany Danych (PWD). The following data products are available via REST API with OAuth 2.0 client credentials grant.

### Generation Data Stream

**API Endpoint:** `GET /api/v1/generation/actual`
**Authentication:** Bearer token (OAuth 2.0, validity 3600s)
**Refresh Rate:** Every 60 seconds
**Retention:** 90 days

| Field | Type | Unit | Description |
|---|---|---|---|
| settlement_period_id | string(8) | YYYYMMDDHHMM | The 15-minute settlement period identifier |
| unit_id | string(16) | — | PSE-assigned generation unit identifier (six-digit KSE code) |
| actual_generation_mw | float | MW | Metered actual generation |
| scheduled_generation_mw | float | MW | Day-ahead scheduled generation (schemat I) |
| generation_type | string(4) | — | Code: BIO, WOD, WIA, PVP, PVS, GAZ, KAM, LNG, ATO, OLE (10 categories) |
| res_flag | boolean | — | True if generation_type is BIO, WOD, WIA, PVP, or PVS |
| balancing_energy_mw | float | MW | Actual - Scheduled (positive = overgeneration) |

The full data product covers approximately 400 generation units. Pipeline ingestion must handle burst patterns at the hour boundary when all 400 units publish simultaneously, producing a burst of approximately 400 × 8 fields × 60 bytes ≈ 192 KB per second, which is well within standard HTTP/2 request throughput.

### Load Data Stream

**API Endpoint:** `GET /api/v1/load/actual`
**Authentication:** Bearer token
**Refresh Rate:** Every 60 seconds
**Retention:** 90 days

| Field | Type | Unit | Description |
|---|---|---|---|
| settlement_period_id | string(8) | YYYYMMDDHHMM | Settlement period identifier |
| national_load_mw | float | MW | Total national load (sum of all DSO-measured consumption) |
| scheduled_load_mw | float | MW | Total scheduled load from DSO schedules |
| balancing_energy_mw | float | MW | Actual - Scheduled load deviation |
| cross_border_flow_mw | float | MW | Net cross-border flow (positive = import) |

Cross-border flow is the critical field for data quality monitoring. Poland has synchronised interconnections with Germany, Czechia, Slovakia, Lithuania, and Sweden (via the SwePol Link). A pipeline failure that drops cross-border flow updates for more than two consecutive settlement periods renders the balancing market data set incomplete for any analysis of price formation, since approximately 15-20% of domestic balancing needs are met through cross-border exchange.

### Imbalance Price Stream

**API Endpoint:** `GET /api/v1/prices/imbalance`
**Authentication:** Bearer token
**Refresh Rate:** Every 15 minutes (published 30 minutes after period close)
**Retention:** 365 days

| Field | Type | Unit | Description |
|---|---|---|---|
| settlement_period_id | string(8) | YYYYMMDDHHMM | Settlement period identifier |
| CREB | float | PLN/MWh | Marginal balancing energy price |
| CRRB | float | PLN/MWh | Volume-weighted reference price |
| imbalance_charge_negative | float | PLN/MWh | max(CREB, CRRB) × absolute deviation |
| imbalance_charge_positive | float | PLN/MWh | min(CREB, CRRB) × absolute deviation |
| total_balancing_energy_mwh | float | MWh | Total activated balancing energy in period |

The imbalance price stream is the highest-latency data product — prices are published 30-45 minutes after the settlement period ends. This means pipeline architectures must handle asynchronous arrival of generation/load data (60s latency) and price data (45-minute latency) without blocking. A kanban-buffer architecture with materialised aggregation windows is the recommended pattern: generation and load data populate a Redis time-series buffer at 60-second granularity, while price data backfills the 96th-period window upon arrival, triggering a recomputation of any derived metrics that depend on price (imbalance cost, RES deviation penalty).

## Pipeline Architecture

### Stream Ingestion Layer

The reference ingestion pipeline for PSE data products must satisfy four latency requirements:

| Data Product | Max Ingestion Latency | Recovery Window | Required Reliability |
|---|---|---|---|
| Generation actual | 120 seconds | 4 hours | 99.5% uptime |
| Load actual | 120 seconds | 4 hours | 99.5% uptime |
| Cross-border flow | 120 seconds | 2 hours | 99.9% uptime |
| Imbalance prices | 60 minutes | 48 hours | 99.0% uptime |

The generation, load, and cross-border flow streams can share a single ingestion worker pool. The imbalance price stream requires a separate worker with a longer poll interval (5 minutes vs 60 seconds) and a backfill trigger for missed periods.

### Data Quality Checks

Each ingested record must pass three data quality gates before entering the analytical store:

**Gate 1 — Schema Conformance:** All required fields present, all numeric fields parseable as floats, timestamps in ISO 8601 format, unit identifiers match the KSE register. Non-conformant records are routed to a dead-letter queue with the original HTTP response body and a timestamp of ingestion failure. The dead-letter queue is the primary mechanism for diagnosing PSE API changes, which occur approximately once per quarter.

**Gate 2 — Range Validation:** `actual_generation_mw` for each unit must be within `[-50, installed_capacity × 1.2]`. Negative values are permitted (pumped storage consumption). Values below -50 MW for non-storage units are hard rejects. `national_load_mw` must be within `[15,000, 35,000]` for the Polish system (minimum base load ~15 GW, maximum peak ~32 GW with export). Values outside this range trigger an immediate re-poll of the PSE API to distinguish data corruption from actual system events.

**Gate 3 — Monotonicity and Gap Detection:** Settlement period IDs must be strictly increasing with no gaps. A missing settlement period is defined as any 15-minute interval without a corresponding record that is more than 5 minutes overdue. After 4 hours of continuous gap detection in a stream, the ingestion worker escalates to a human operator via the incident management system. This threshold (4 hours) corresponds to the recovery window in the latency requirements table above — if the gap exceeds the recovery window, the data is permanently lost and cannot be reconstructed.

### Storage Schema

```sql
CREATE TABLE pse_generation_actual (
    settlement_period_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    actual_generation_mw REAL NOT NULL,
    scheduled_generation_mw REAL,
    generation_type TEXT NOT NULL,
    res_flag INTEGER NOT NULL DEFAULT 0,
    balancing_energy_mw REAL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (settlement_period_id, unit_id)
);

CREATE TABLE pse_load_actual (
    settlement_period_id TEXT NOT NULL PRIMARY KEY,
    national_load_mw REAL NOT NULL,
    scheduled_load_mw REAL,
    balancing_energy_mw REAL,
    cross_border_flow_mw REAL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pse_imbalance_prices (
    settlement_period_id TEXT NOT NULL PRIMARY KEY,
    creb REAL NOT NULL,
    crrb REAL NOT NULL,
    imbalance_charge_negative REAL,
    imbalance_charge_positive REAL,
    total_balancing_energy_mwh REAL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pse_ingestion_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_name TEXT NOT NULL,
    settlement_period_id TEXT,
    ingestion_status TEXT NOT NULL CHECK(ingestion_status IN ('success', 'failed', 'backfilled')),
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

This schema is minimal by design — OLAP queries are executed against materialised views, not raw tables. The raw tables serve as the entry store for the ETL pipeline and as the source of truth for data quality audits. Materialised views are rebuilt on a 15-minute cycle aligned with the settlement period boundary.

### RES Forecasting Correction Pipeline

The critical pipeline component for RES integration is the forecasting correction layer. PSE publishes day-ahead generation schedules (schemat I) for each RES unit. The ingestion pipeline compares schemat I against actual generation for each settlement period and computes the deviation:

`delta(i, t) = actual(i, t) - scheduled(i, t)`

The `delta` values are aggregated by generation type and region into a real-time RES forecast error signal. This signal is published as a separate data product to downstream consumers (trading desks, balancing-responsible entities, regulatory authorities). The mean forecast error per RES type is a key input to the daily imbalance price prediction model maintained by the Polish Power Exchange (TGE).

A persistent negative `delta` (actual generation below scheduled) for wind or solar indicates either an overoptimistic day-ahead forecast or an unplanned curtailment. PSE is required to report generation curtailments to the Energy Regulatory Office (URE) within 30 days. The pipeline automatically flags any RES unit with `delta < -0.2 × installed_capacity` for three consecutive settlement periods as a potential curtailment event requiring URE notification.

## Implementation Constraints

**Clock synchronisation:** All timestamps in PSE data products use Central European Time (CET/CEST) without explicit timezone markers. Pipelines must maintain their system clock synchronised via NTP and must handle the CET/CEST transition on the last Sunday of March and October. A pipeline that fails to account for the 02:00-03:00 spring-forward gap will produce corrupted settlement period IDs for approximately 4 hours (16 settlement periods) each year.

**Rate limiting:** The PSE PWD API permits 60 requests per minute per client credential. At a 60-second poll interval across three streams (generation, load, prices), the pipeline makes exactly 3 requests per minute — well within the limit. However, the backfill mechanism for missed periods must throttle its catch-up poll rate to avoid exceeding the limit during recovery windows.

**Data retention:** PSE retains generation and load data for 90 days on the API. Pipelines requiring historical comparisons (e.g., year-over-year RES integration analysis) must implement their own long-term storage. The reference implementation stores raw PSE data in compressed Parquet files partitioned by month, with 10:1 compression ratio achievable for numeric time-series data.

---

**Last Updated:** 2026-06-29  
**Version:** 1.0.0  
**Classification:** Internal Technical Documentation  
**Primary Source Authority:** PSE S.A. PWD API Specification v2.4, Polish Energy Law (Prawo Energetyczne) Art. 101-112, URE Balancing Market Regulations  
**Confidence Score:** 0.93  
**Ontology Tag:** energy/pse-balancing-market
