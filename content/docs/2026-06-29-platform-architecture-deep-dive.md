---
title: Platform Architecture Deep Dive
slug: docs/platform-architecture
category: knowledge
pillar: data-engineering
tags: [architecture, dataops, knowledge-graph, agentic-systems, llmops]
author: AcaciaFund
date: 2026-06-29
sqi: 0.92
---

# Platform Architecture Deep Dive

A comprehensive technical specification of the five-layer AcaciaFund platform architecture, detailing data flows, component interactions, and operational patterns for senior engineering audiences.

## Executive Summary

AcaciaFund operates as a sovereign data pipeline engineered for financial intelligence and compliance operations. The platform follows a strict five-layer architecture designed to ensure data integrity, operational transparency, and human oversight at every decision point.

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                              │
│         (HackerNews API / Public Med)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE GRAPH LAYER                        │
│  RDF/Property Graph Hybrid | Schema Enforcement | Entity        │
│  Resolution (Levenshtein + Vector Embeddings)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
│         Object Storage (S3/R2) | Apache Iceberg | Time-Travel   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTIC LAYER                               │
│         ReAct Loops | State Machine Orchestration | NVIDIA NIM  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EVALUATION LAYER                             │
│        6-Dim Quality Gate | Bayesian Inference | LSP Linting    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HUMAN OVERSIGHT LAYER                         │
│    Zero-JS Interface | Expert Escalation | Deterministic        │
│    Overrides                                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Layer 1: Knowledge Graph Layer

### Architecture Overview

The Knowledge Graph Layer serves as the semantic backbone of the platform, unifying disparate data sources into a coherent entity-relationship model. It employs a hybrid RDF/Property Graph architecture to leverage the strengths of both models: RDF for triple-based reasoning and Property Graphs for high-performance querying.

### Schema Enforcement

All entities must conform to a strict schema defined in `schemas.py`:

```python
ENTITY_SCHEMA = {
    "entities": {
        "type": "object",
        "required": ["id", "name", "type", "confidence"],
        "properties": {
            "id": {"type": "string", "pattern": "^[a-z0-9_-]+$"},
            "name": {"type": "string", "minLength": 1, "maxLength": 256},
            "type": {"type": "string", "enum": ["person", "organization", "transaction", "document", "location"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "sources": {"type": "array", "items": {"type": "string"}},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        }
    }
}
```

### Entity Resolution

Entity resolution employs a multi-stage approach combining deterministic and probabilistic methods:

#### Stage 1: Levenshtein Distance Matching

For string similarity-based entity matching, we apply normalized Levenshtein Distance with a configurable threshold:

```python
def levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculate normalized Levenshtein similarity (0.0-1.0)"""
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (distance / max_len) if max_len > 0 else 1.0

# Threshold configuration
ENTITY_MATCH_THRESHOLD = 0.85  # 85% similarity required for merge
```

**Parameters:**
- Threshold: 0.85 (85% similarity)
- Case-insensitive normalization
- Whitespace and punctuation normalization

#### Stage 2: Vector Embedding Cosine Similarity

For semantic similarity beyond string matching, we utilize pre-trained embeddings:

```python
def vector_similarity(entity1: Entity, entity2: Entity) -> float:
    """Calculate cosine similarity between entity embeddings"""
    embedding1 = model.encode(entity1.name)
    embedding2 = model.encode(entity2.name)
    return cosine_similarity(embedding1, embedding2)

# Semantic threshold
SEMANIC_MATCH_THRESHOLD = 0.75  # 75% semantic similarity
```

**Implementation Details:**
- Model: `all-MiniLM-L6-v2` (6-layer BERT, 384-dimensional)
- Batch processing for performance
- Cache hits for repeated queries
- Fallback to Levenshtein if embedding unavailable

#### Stage 3: Confidence Scoring

Final entity match confidence combines both methods:

```python
def calculate_match_confidence(levenshtein_score: float, vector_score: float, 
                               context_evidence: int) -> float:
    """
    Calculate weighted confidence score for entity matching.
    
    Args:
        levenshtein_score: Normalized string similarity (0.0-1.0)
        vector_score: Cosine similarity of embeddings (0.0-1.0)
        context_evidence: Number of supporting context signals
    
    Returns:
        Weighted confidence score (0.0-1.0)
    """
    # Base weights: string match 60%, semantic 40%
    base_confidence = (levenshtein_score * 0.6) + (vector_score * 0.4)
    
    # Context evidence multiplier
    context_multiplier = min(1.0, 1.0 + (context_evidence * 0.1))
    
    return min(1.0, base_confidence * context_multiplier)
```

### Graph Storage

The hybrid storage approach:

- **RDF Store:** Neo4j for triple-based reasoning and SPARQL queries
- **Property Graph:** Neo4j for Cypher queries and high-performance lookups
- **Indexing:** Lucene for full-text search on entity names
- **Partitioning:** Sharded by entity type for horizontal scaling

## Layer 2: Data Layer

### Object Storage Pattern

The platform employs Cloudflare R2 as primary object storage with S3 compatibility:

```python
# Storage configuration
STORAGE_CONFIG = {
    "provider": "cloudflare_r2",
    "bucket": "acaciafund-data",
    "region": "auto",
    "encryption": "AES-256-GCM",
    "versioning": True,
    "lifecycle": {
        "transition_to_iceberg": "30_days",
        "archive_to_glacier": "1_year"
    }
}
```

**Key Features:**
- Zero egress fees (Cloudflare R2 advantage)
- S3 API compatibility
- Server-side encryption at rest
- Automatic versioning for data lineage

### Apache Iceberg Table Format

For structured data requiring ACID compliance, we use Apache Iceberg:

```python
# Iceberg table configuration
ICEBERG_CONFIG = {
    "format_version": "2.0",
    "write_format": "snap",
    "read_format": "snap",
    "schema_evolution": True,
    "partitioning": [
        {"field": "date_created", "transform": "bucket(16)"},
        {"field": "entity_type", "transform": "identity"}
    ],
    "metadata_location": "s3://acaciafund-data/{table}/metadata/",
    "data_location": "s3://acaciafund-data/{table}/data/"
}
```

**ACID Guarantees:**
- Atomic writes via snapshot isolation
- Consistent reads with snapshot versioning
- Isolation between concurrent transactions
- Durability through write-ahead logging

### Time-Travel Queries

Iceberg enables historical data access without data duplication:

```python
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("acaciafund", **CREDENTIALS)

# Time-travel query to specific timestamp
snapshot = catalog.load_snapshot("transactions", "2026-06-28T00:00:00Z")
df = table.load(snapshot=snapshot.id).to_pandas()

# Query with time travel syntax
df = table.select(
    "id", "amount", "counterparty"
).filter("amount > 10000")
# Returns data as of latest snapshot by default

# Specific version
df_v2 = table.select("id", "amount").filter("amount > 10000")
df_v2 = df_v2.set_options(iceberg_time_travel="2026-06-27T00:00:00Z")
```

**Use Cases:**
- Regulatory audit trails
- Data quality regression testing
- Compliance reporting with historical context
- Reproducible analysis environments

### Data Lineage Tracking

Every transformation is logged with full lineage:

```python
class DataLineageTracker:
    def __init__(self):
        self.lineage_events = []
    
    def track_transformation(self, source: str, operation: str, 
                            target: str, parameters: dict):
        """Log transformation event with full context"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "operation": operation,
            "target": target,
            "parameters": parameters,
            "operator": os.getenv("OPERATOR_ID"),
            "version": os.getenv("GIT_COMMIT")
        }
        self.lineage_events.append(event)
        # Persist to Iceberg metadata table
        self._persist_to_lineage_table(event)
```

## Layer 3: Agentic Layer

### ReAct Loop Architecture

The Agentic Layer implements ReAct (Reasoning and Action) loops for intelligent data processing:

```python
class ReActAgent:
    def __init__(self, llm_endpoint: str, tools: list):
        self.llm_endpoint = llm_endpoint
        self.tools = tools
        self.max_iterations = 10
        self.temperature = 0.2  # Low temperature for deterministic outputs
    
    def reason_and_act(self, query: str, context: dict) -> dict:
        """Execute ReAct loop for query resolution"""
        observation = context
        history = []
        
        for iteration in range(self.max_iterations):
            # REASON: Generate thought and action plan
            reason_response = self._call_llm(
                prompt=self._build_reason_prompt(query, observation, history),
                temperature=self.temperature
            )
            thought, action = self._parse_reason_response(reason_response)
            
            history.append({
                "iteration": iteration,
                "thought": thought,
                "action": action
            })
            
            if action == "final":
                break
            
            # ACT: Execute selected tool
            observation = self._execute_action(action, observation)
        
        return {
            "query": query,
            "observations": observation,
            "history": history,
            "iterations": len(history)
        }
    
    def _build_reason_prompt(self, query: str, observation: dict, 
                            history: list) -> str:
        """Construct ReAct reasoning prompt"""
        return f"""
        You are an intelligent data analyst. Analyze the observation and decide the next action.
        
        Query: {query}
        Current Observation: {observation}
        Previous Actions: {history}
        
        Available Tools: {self.tools}
        
        Reason through the problem step by step. Decide whether to:
        1. Use a tool to gather more information
        2. Synthesize existing information
        3. Declare final answer
        
        Format your response as JSON with 'thought' and 'action' fields.
        """
```

### State Machine Orchestration

Complex workflows are orchestrated via customized state machines:

```python
from enum import Enum
from typing import Dict, List, Callable

class WorkflowState(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    ENRICHING = "enriching"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"

class StateMachine:
    def __init__(self, initial_state: WorkflowState):
        self.current_state = initial_state
        self.transitions: Dict[WorkflowState, Dict[WorkflowState, Callable]] = {}
        self.history: List[dict] = []
    
    def add_transition(self, from_state: WorkflowState, to_state: WorkflowState,
                      handler: Callable):
        """Register state transition with handler"""
        if to_state not in self.transitions[from_state]:
            self.transitions[from_state][to_state] = []
        self.transitions[from_state][to_state].append(handler)
    
    def transition(self, event: str, data: dict = None) -> WorkflowState:
        """Execute state transition based on event"""
        old_state = self.current_state
        new_state = self.current_state  # Default: no change
        
        # Find matching transition
        for target_state, handlers in self.transitions[old_state].items():
            for handler in handlers:
                if handler(event, data):
                    new_state = target_state
                    self._log_transition(old_state, new_state, event, data)
                    break
        
        self.current_state = new_state
        return new_state
    
    def _log_transition(self, from_state: WorkflowState, to_state: WorkflowState,
                       event: str, data: dict):
        """Log state transition for audit trail"""
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "from_state": from_state.value,
            "to_state": to_state.value,
            "event": event,
            "data": data
        })
```

### NVIDIA NIM Endpoint Integration

The platform utilizes NVIDIA NIM (NVIDIA Inference Microservices) for LLM inference:

```python
import requests

class NIMClient:
    def __init__(self, api_key: str, organization: str):
        self.api_key = api_key
        self.organization = organization
        self.base_url = f"https://integrate.api.nvidia.com/v1"
    
    def call_completion(self, model: str, prompt: str, 
                       system_prompt: str = None, 
                       max_tokens: int = 512) -> dict:
        """Invoke NVIDIA NIM completion endpoint"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-NVIDIA-ORGANIZATION": self.organization
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "top_p": 0.9
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
```

**Supported Models:**
- `meta/llama3-70b-instruct`
- `mistralai/mixtral-8x7b-instruct-v0.1`
- `nvidia/nemotron-4-340b-instruct`

## Layer 4: Evaluation Layer

### 6-Dimension Quality Gate

Every piece of content must pass through the 6-Dimension Quality Gate before publication:

```python
class QualityGate:
    def __init__(self):
        self.dimensions = {
            "VALIDATE": self._validate_content,
            "VALUE": self._assess_value,
            "TRANSFORM": self._check_transformations,
            "STORAGE": self._verify_storage,
            "VISUAL": self._validate_visuals,
            "RENDER": self._check_rendering
        }
    
    def evaluate(self, content: dict) -> dict:
        """Run full quality gate evaluation"""
        results = {}
        scores = []
        
        for dimension, evaluator in self.dimensions.items():
            result = evaluator(content)
            results[dimension] = result
            scores.append(result["score"])
        
        # Weighted average with dimensional weights
        weights = {
            "VALIDATE": 0.25,
            "VALUE": 0.25,
            "TRANSFORM": 0.20,
            "STORAGE": 0.10,
            "VISUAL": 0.10,
            "RENDER": 0.10
        }
        
        overall_score = sum(s * w for s, w in zip(scores, weights.values()))
        
        return {
            "overall_score": overall_score,
            "dimension_scores": dict(zip(self.dimensions.keys(), scores)),
            "passed": overall_score >= 0.7,  # 70% threshold
            "details": results
        }
    
    def _validate_content(self, content: dict) -> dict:
        """Validate content structure and integrity"""
        errors = []
        warnings = []
        
        # Check required fields
        required = ["title", "content", "slug", "category", "tags"]
        for field in required:
            if field not in content:
                errors.append(f"Missing required field: {field}")
        
        # Validate markdown syntax
        if content.get("content"):
            try:
                commonmark.render(content["content"])
            except Exception as e:
                errors.append(f"Invalid markdown: {str(e)}")
        
        score = 1.0 - (len(errors) * 0.1) - (len(warnings) * 0.05)
        return {"score": max(0.0, score), "errors": errors, "warnings": warnings}
    
    def _assess_value(self, content: dict) -> dict:
        """Assess content value using Bayesian inference"""
        # Bayesian prior: high-quality content has certain characteristics
        prior_probability = 0.3  # Base rate of high-quality content
        
        # Likelihoods based on content features
        likelihoods = []
        
        if len(content.get("tags", [])) >= 3:
            likelihoods.append(0.8)  # Good tag coverage
        else:
            likelihoods.append(0.3)
        
        if content.get("content") and len(content["content"]) > 1000:
            likelihoods.append(0.9)  # Substantial content
        else:
            likelihoods.append(0.4)
        
        # Posterior probability using Bayes' theorem
        likelihood_avg = sum(likelihoods) / len(likelihoods)
        posterior = (likelihood_avg * prior_probability) / (likelihood_avg * prior_probability + (1 - prior_probability))
        
        score = min(1.0, posterior / 0.5)  # Normalize to 0-1 scale
        return {"score": score, "posterior_probability": posterior}
```

### Bayesian Inference for Source Validation

Source credibility is assessed using Bayesian inference:

```python
class BayesianSourceValidator:
    def __init__(self):
        self.source_priors = {
            "official": 0.8,      # Government/regulatory sources
            "academic": 0.7,      # Peer-reviewed publications
            "industry": 0.5,      # Industry reports
            "media": 0.4,         # News outlets
            "blog": 0.3           # Individual blogs
        }
    
    def validate_source(self, source_type: str, evidence: list) -> float:
        """
        Calculate posterior probability of source credibility.
        
        Args:
            source_type: Category of source (official, academic, etc.)
            evidence: List of evidence signals supporting credibility
        
        Returns:
            Posterior credibility score (0.0-1.0)
        """
        # Prior probability based on source type
        prior = self.source_priors.get(source_type, 0.5)
        
        # Likelihood ratio for each evidence signal
        likelihood_ratios = {
            "citations": 3.0,      # 3x more likely if cited
            "peer_review": 5.0,    # 5x more likely if peer-reviewed
            "author_expertise": 2.0,
            "transparency": 2.5,   # 2.5x more likely if transparent
            "corroboration": 4.0    # 4x more likely if corroborated
        }
        
        # Calculate likelihood ratio from evidence
        lr = 1.0
        for signal in evidence:
            lr *= likelihood_ratios.get(signal, 1.0)
        
        # Bayes' theorem: P(H|E) = P(E|H) * P(H) / P(E)
        # Simplified: posterior = (lr * prior) / (lr * prior + (1 - prior))
        posterior = (lr * prior) / (lr * prior + (1 - prior))
        
        return min(1.0, posterior)
```

### Automated LSP Integrity Linting

Code and configuration files undergo automated linting:

```python
import subprocess
import json

class LSPIntegrityChecker:
    def __init__(self):
        self.languages = {
            "python": {"linter": "ruff", "formatter": "black"},
            "javascript": {"linter": "eslint", "formatter": "prettier"},
            "yaml": {"linter": "yamllint", "formatter": "prettier"},
            "markdown": {"linter": "markdownlint", "formatter": "none"}
        }
    
    def lint_file(self, filepath: str, language: str) -> dict:
        """Run LSP-based linting on file"""
        if language not in self.languages:
            return {"errors": [], "warnings": [], "message": f"Unsupported language: {language}"}
        
        linter = self.languages[language]["linter"]
        output = subprocess.run(
            [linter, "--format", filepath],
            capture_output=True,
            text=True
        )
        
        errors = []
        warnings = []
        
        for line in output.stdout.split('\n'):
            if 'error' in line.lower():
                errors.append(line)
            elif 'warning' in line.lower():
                warnings.append(line)
        
        return {
            "errors": errors,
            "warnings": warnings,
            "passed": len(errors) == 0
        }
```

## Layer 5: Human Oversight Layer

### Zero-JS Progressive Enhancement Interface

The oversight interface follows progressive enhancement principles:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Human Oversight Dashboard</title>
    <style>
        /* Critical CSS - Works without JavaScript */
        .oversight-container {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            padding: 1rem;
        }
        
        .oversight-item {
            border: 1px solid #ccc;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .oversight-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .btn-approve { background: #22c55e; color: white; }
        .btn-reject { background: #ef4444; color: white; }
        .btn-escalate { background: #f59e0b; color: white; }
    </style>
</head>
<body>
    <div class="oversight-container">
        <!-- Content rendered server-side -->
        <h1>Human Oversight Dashboard</h1>
        
        <div class="oversight-item" data-id="item-1">
            <h3>Agent Output Requiring Review</h3>
            <p>Analysis of transaction TX-2026-0629-001</p>
            <div class="oversight-actions">
                <button class="btn btn-approve" data-action="approve">Approve</button>
                <button class="btn btn-reject" data-action="reject">Reject</button>
                <button class="btn btn-escalate" data-action="escalate">Escalate</button>
            </div>
        </div>
    </div>
    
    <!-- Progressive enhancement: JavaScript adds interactivity -->
    <script>
        // Only enhances if JavaScript is available
        document.addEventListener('DOMContentLoaded', function() {
            const buttons = document.querySelectorAll('.oversight-actions button');
            buttons.forEach(btn => {
                btn.addEventListener('click', function() {
                    const action = this.dataset.action;
                    const itemId = this.closest('.oversight-item').dataset.id;
                    
                    fetch('/api/oversight/' + itemId + '/' + action, {
                        method: 'POST'
                    });
                });
            });
        });
    </script>
</body>
</html>
```

### Expert Escalation Pathways

Multi-tier escalation for complex cases:

```python
class EscalationManager:
    def __init__(self):
        self.tiers = {
            "tier_1": {
                "level": 1,
                "capacity": 100,
                "sla_minutes": 30,
                "expertise": ["general_compliance", "basic_aml"]
            },
            "tier_2": {
                "level": 2,
                "capacity": 20,
                "sla_minutes": 60,
                "expertise": ["complex_transactions", "cross_border", "sanctions"]
            },
            "tier_3": {
                "level": 3,
                "capacity": 5,
                "sla_minutes": 120,
                "expertise": ["regulatory_reporting", "high_risk_clients", "international"]
            }
        }
    
    def get_appropriate_tier(self, case: dict) -> str:
        """Determine escalation tier based on case characteristics"""
        risk_score = case.get("risk_score", 0.5)
        complexity = case.get("complexity", 1)
        jurisdiction_count = len(case.get("jurisdictions", []))
        
        # Simple decision logic
        if risk_score > 0.8 or complexity > 3 or jurisdiction_count > 2:
            return "tier_3"
        elif risk_score > 0.5 or complexity > 2 or jurisdiction_count > 1:
            return "tier_2"
        else:
            return "tier_1"
    
    def escalate_case(self, case_id: str, current_tier: str, 
                     reason: str) -> dict:
        """Escalate case to next tier"""
        current = self.tiers[current_tier]
        
        # Find next tier
        tier_order = ["tier_1", "tier_2", "tier_3"]
        current_index = tier_order.index(current_tier)
        
        if current_index >= len(tier_order) - 1:
            return {"error": "Maximum escalation tier reached"}
        
        next_tier = tier_order[current_index + 1]
        
        # Create escalation record
        escalation = {
            "case_id": case_id,
            "from_tier": current_tier,
            "to_tier": next_tier,
            "reason": reason,
            "escalated_by": os.getenv("OPERATOR_ID"),
            "escalated_at": datetime.utcnow().isoformat(),
            "original_sla": current["sla_minutes"],
            "new_sla": self.tiers[next_tier]["sla_minutes"]
        }
        
        # Persist escalation
        self._persist_escalation(escalation)
        
        return {"success": True, "next_tier": next_tier}
```

### Deterministic Overrides for Agent Outputs

Human operators can override agent decisions with deterministic controls:

```python
class DeterministicOverride:
    def __init__(self):
        self.override_log = []
    
    def apply_override(self, case_id: str, agent_decision: dict, 
                      human_decision: dict, reason: str) -> dict:
        """Apply deterministic human override to agent output"""
        
        # Create override record
        override = {
            "case_id": case_id,
            "agent_decision": agent_decision,
            "human_decision": human_decision,
            "reason": reason,
            "overridden_by": os.getenv("OPERATOR_ID"),
            "overridden_at": datetime.utcnow().isoformat(),
            "override_type": human_decision.get("type", "manual"),
            "confidence_delta": abs(
                human_decision.get("confidence", 0.5) - 
                agent_decision.get("confidence", 0.5)
            )
        }
        
        self.override_log.append(override)
        
        # Persist to audit log
        self._persist_to_audit_log(override)
        
        # Update case state
        self._update_case_decision(case_id, human_decision)
        
        return override
    
    def get_override_statistics(self) -> dict:
        """Generate override statistics for quality analysis"""
        if not self.override_log:
            return {"total": 0, "by_type": {}, "by_tier": {}}
        
        by_type = {}
        by_tier = {}
        
        for override in self.override_log:
            override_type = override["override_type"]
            tier = override["human_decision"].get("tier", "unknown")
            
            by_type[override_type] = by_type.get(override_type, 0) + 1
            by_tier[tier] = by_tier.get(tier, 0) + 1
        
        return {
            "total": len(self.override_log),
            "by_type": by_type,
            "by_tier": by_tier,
            "override_rate": len(self.override_log) / max(1, len(self.override_log) + 100)
        }
```

## Integration Patterns

### Inter-Layer Communication

Layers communicate via well-defined APIs:

```python
# Layer 1 -> Layer 2: Ingested data to Knowledge Graph
def ingest_to_knowledge_graph(data: dict) -> str:
    """Submit data for Knowledge Graph processing"""
    return requests.post(
        "http://kg-service/api/ingest",
        json=data,
        headers={"Authorization": "Bearer " + os.getenv("KG_API_KEY")}
    ).json()["snapshot_id"]

# Layer 2 -> Layer 3: Enriched data to Agentic Layer
def query_agentic_layer(query: str, context: dict) -> dict:
    """Query Agentic Layer for intelligent processing"""
    return requests.post(
        "http://agentic-service/api/query",
        json={"query": query, "context": context},
        headers={"Authorization": "Bearer " + os.getenv("AGENT_API_KEY")}
    ).json()["response"]

# Layer 3 -> Layer 4: Agent outputs to Evaluation Layer
def evaluate_agent_output(output: dict) -> dict:
    """Evaluate agent output against quality gates"""
    return requests.post(
        "http://evaluation-service/api/evaluate",
        json=output,
        headers={"Authorization": "Bearer " + os.getenv("EVAL_API_KEY")}
    ).json()["evaluation"]

# Layer 4 -> Layer 5: Evaluated content to Human Oversight
def submit_for_human_review(content: dict, evaluation: dict) -> str:
    """Submit content requiring human review"""
    return requests.post(
        "http://oversight-service/api/submit",
        json={"content": content, "evaluation": evaluation},
        headers={"Authorization": "Bearer " + os.getenv("OVERSIGHT_API_KEY")}
    ).json()["review_id"]
```

## Performance Characteristics

| Layer | Latency | Throughput | Availability |
|-------|---------|------------|--------------|
| Knowledge Graph | <50ms | 10K QPS | 99.9% |
| Data Layer | <100ms | 100K QPS | 99.95% |
| Agentic Layer | 200-500ms | 1K QPS | 99.5% |
| Evaluation Layer | <50ms | 5K QPS | 99.9% |
| Human Oversight | N/A | 100 concurrent | 99.9% |

## Security Considerations

- **Data Encryption:** AES-256-GCM at rest, TLS 1.3 in transit
- **Access Control:** RBAC with least-privilege principle
- **Audit Logging:** Immutable audit trail for all operations
- **Secrets Management:** HashiCorp Vault for sensitive data
- **Network Segmentation:** Zero-trust architecture between layers

---

**Last Updated:** 2026-06-29  
**Version:** 1.0.0  
**Classification:** Internal Technical Documentation
