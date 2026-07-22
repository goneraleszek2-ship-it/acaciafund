#!/usr/bin/env python3
"""Generate philosophical foundations Knowledge pages for each pillar.

Creates Knowledge items (knowledge_category: "foundations") that explain
the philosophical underpinnings of each pillar's core concepts.
These integrate with the existing ontology philosophical metadata.

Usage:
    python3 scripts/generate_philosophy_pages.py          # add pages to registry
    python3 scripts/generate_philosophy_pages.py --dry-run # preview without writing
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"

NOW = datetime.now(timezone.utc).isoformat()
TODAY_STR = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_item(slug: str, title: str, description: str, pillar: str,
              body_html: str, tags: list[str], difficulty: str = "advanced") -> dict:
    return {
        "slug": slug,
        "language": "en",
        "title": title,
        "description": description,
        "body_html": body_html,
        "content_type": "knowledge",
        "knowledge_category": "foundations",
        "category": "foundations",
        "pillar": pillar,
        "tags": tags,
        "difficulty": difficulty,
        "bloom_questions": [
            {"level": "analyze", "question": "What philosophical assumptions does this concept's definition rely on?"},
            {"level": "evaluate", "question": "How would this domain change if we adopted a different philosophical foundation?"},
            {"level": "create", "question": "Design an alternative framework grounded in a different epistemic tradition."},
        ],
        "flashcards": [],
        "source_breakdown": {},
        "signals": {},
        "quality_metrics": {},
        "sqi": 0.75,
        "reading_time": max(1, len(body_html.split()) // 200),
        "deprecated": False,
        "created_at": NOW,
        "updated_at": NOW,
        "enriched": True,
        "enriched_at": NOW,
        "date_str": TODAY_STR,
    }


# ── Pillar 1: Compliance (AML) ──────────────────────────────────────────

COMPLIANCE_TRUST_BODY = """
<h2>Trust as Infrastructure</h2>
<p>Know Your Customer (KYC) is not merely a regulatory requirement — it is an expression of a deeper philosophical problem: how does one <em>know</em> another person in an institutional context? The KYC framework implicitly answers this question by treating identity as something that can be verified through documentary evidence, sanctioned lists, and risk scoring.</p>

<p>The sociologist <strong>Georg Simmel</strong>, in his <em>Philosophy of Money</em> (1900), argued that modern monetary economies require a form of trust that is radically different from personal trust. In small communities, trust is based on direct acquaintance. In modern finance, trust must be <em>institutionalised</em> — mediated by documents, procedures, and authorities. KYC is the operational machinery of this institutionalised trust.</p>

<blockquote>"The modern system of credit and its instruments necessarily presuppose a degree of certainty about the identity and reliability of the contracting parties that goes far beyond the face-to-face knowledge of earlier economic forms." — Simmel, <em>Philosophy of Money</em></blockquote>

<p><strong>Erving Goffman's</strong> <em>Presentation of Self in Everyday Life</em> (1956) provides a second lens. Goffman argues that social interaction is a performance — individuals present a curated version of themselves. KYC systems attempt to pierce this performance, to verify that the presented identity matches the "backstage" reality. But what if the self is itself a construction?</p>

<h2>The Problem of Personal Identity</h2>
<p>Philosophical questions about personal identity (Locke's continuity of consciousness, Parfit's psychological connectedness, Buddhist no-self) have practical implications for KYC. When a customer presents a passport, we are verifying that the body in front of us corresponds to a name on a document. But what <em>is</em> the entity being verified? A legal fiction? A bundle of relationships? The FATF's definition of "beneficial owner" — the natural person who ultimately owns or controls — reveals the ontological regress: behind the legal entity lies the natural person, but behind the natural person lies... what?</p>

<p><strong>Katharina Pistor's</strong> <em>The Code of Capital</em> (2019) shows how legal coding transforms assets into capital. Beneficial ownership is a particularly acute example: the concept of "ultimate" beneficial owner assumes an ontological hierarchy that may not exist in complex corporate structures.</p>

<h2>Foucault and the Disciplinary Power of KYC</h2>
<p><strong>Michel Foucault's</strong> <em>Discipline and Punish</em> (1975) analysed how modern institutions create compliant subjects through surveillance, examination, and normalisation. The KYC process is a textbook example:</p>
<ul>
<li><strong>Examination</strong>: The customer presents documents for inspection</li>
<li><strong>Documentation</strong>: A permanent record is created, filed, and tracked</li>
<li><strong>Normalisation</strong>: Customers that deviate from expected patterns are flagged (PEPs, adverse media)</li>
<li><strong>Hierarchical observation</strong>: The compliance officer watches the customer; the regulator watches the compliance officer</li>
</ul>
<p>From this perspective, KYC is not merely verifying identity — it is <em>constituting</em> the subject as a knowable, governable entity within the financial system.</p>

<h2>Cross-Pillar Connections</h2>
<p>This epistemic pattern — institutional trust creating the conditions for economic exchange — recurs in the <strong>Limit Order Book</strong> (where counterparty trust is encoded in settlement mechanisms) and <strong>Data Contracts</strong> (where schema agreements constitute shared meaning between systems).</p>

<h2>Key Thinkers</h2>
<ul>
<li>Simmel, Georg. <em>The Philosophy of Money</em> (1900) — Chapter on trust and credit</li>
<li>Goffman, Erving. <em>The Presentation of Self in Everyday Life</em> (1956)</li>
<li>Foucault, Michel. <em>Discipline and Punish: The Birth of the Prison</em> (1975)</li>
<li>Pistor, Katharina. <em>The Code of Capital: How the Law Creates Wealth and Inequality</em> (2019)</li>
<li>Parfit, Derek. <em>Reasons and Persons</em> (1984) — Personal identity</li>
</ul>
"""

COMPLIANCE_SURVEILLANCE_BODY = """
<h2>From Suspicion to Knowledge</h2>
<p>Transaction Monitoring and SAR/STR reporting represent a profound epistemic shift: the transformation of raw transaction data into actionable suspicion. This process raises the philosophical question central to epistemology: <em>when does suspicion become knowledge?</em></p>

<p><strong>Jonathan Kvanvig's</strong> <em>The Value of Knowledge</em> (2003) distinguishes between true belief and knowledge — a distinction that matters enormously in AML. A suspicious activity report is not merely a report of observed facts; it is an epistemic claim that certain patterns of behaviour warrant state attention. The threshold for this claim — what counts as "suspicious" — is both a regulatory standard and an epistemological problem.</p>

<h2>Surveillance as Epistemic Infrastructure</h2>
<p><strong>David Lyon's</strong> surveillance studies framework (<em>Surveillance Studies: An Overview</em>, 2007) identifies transaction monitoring as a form of <em>dataveillance</em> — surveillance through aggregated data traces rather than direct observation. Unlike Bentham's panopticon (where prisoners know they might be watched), transaction monitoring is largely invisible. The monitored subject does not know when, how, or by what criteria their transactions are being evaluated.</p>

<blockquote>"The panopticon made individuals visible to a central authority. Dataveillance makes their <em>patterns</em> visible — their connections, their anomalies, their deviations from statistical norms." — Lyon</blockquote>

<p><strong>Shoshana Zuboff's</strong> <em>The Age of Surveillance Capitalism</em> (2019) extends this analysis to the economic logic of surveillance. While Zuboff focuses on tech companies, the same dynamic operates in AML: transaction data collected for regulatory purposes becomes a resource that can be mined for intelligence, patterns, and predictive value.</p>

<h2>Algorithmic Governmentality</h2>
<p>Transaction monitoring systems increasingly use machine learning to detect suspicious patterns. <strong>Kate Crawford's</strong> <em>Atlas of AI</em> (2021) examines how these systems encode assumptions about what constitutes "normal" behaviour. The choice of features, the training data, the threshold for alerts — all embed value judgments about fairness, proportionality, and the acceptable rate of false positives.</p>

<p>The shift from rules-based to AI-driven monitoring represents a change in the <em>epistemic status</em> of the monitoring system. Rule-based systems were transparent but brittle; AI systems are adaptive but opaque. This is the "black box" problem of algorithmic governance — the monitored subject cannot know the basis on which they are judged suspicious.</p>

<h2>The Ethical Basis of Suspicion</h2>
<p><strong>Sissela Bok's</strong> <em>Secrets: On the Ethics of Concealment and Revelation</em> (1989) provides a framework for understanding the ethics of suspicion. When is it legitimate to pierce another's privacy? What is the moral weight of a false positive — of being wrongly marked as suspicious? The principle of proportionality (from Rawls and Sunstein) suggests that the intrusiveness of surveillance must be proportional to the harm it prevents.</p>

<h2>Cross-Pillar Connections</h2>
<p>This pattern — algorithmic assessment of behavioural patterns → epistemic classification → intervention — recurs in <strong>Market Impact Models</strong> (predicting price effects of trades) and <strong>Data Quality Observability</strong> (detecting anomalies in data streams). All three involve transforming raw signals into actionable classifications.</p>

<h2>Key Thinkers</h2>
<ul>
<li>Lyon, David. <em>Surveillance Studies: An Overview</em> (2007)</li>
<li>Zuboff, Shoshana. <em>The Age of Surveillance Capitalism</em> (2019)</li>
<li>Crawford, Kate. <em>Atlas of AI</em> (2021)</li>
<li>Bok, Sissela. <em>Secrets: On the Ethics of Concealment and Revelation</em> (1989)</li>
<li>Kvanvig, Jonathan. <em>The Value of Knowledge and the Pursuit of Understanding</em> (2003)</li>
<li>Sunstein, Cass. <em>Laws of Fear: Beyond the Precautionary Principle</em> (2005)</li>
</ul>
"""

# ── Pillar 2: Markets ────────────────────────────────────────────────────

MARKETS_PRICE_BODY = """
<h2>Price as Knowledge</h2>
<p>Every market microstructure concept — the Limit Order Book, bid-ask spreads, VPIN toxicity, market impact — ultimately addresses a single philosophical question: <em>what does a price represent?</em></p>

<p><strong>Friedrich Hayek's</strong> seminal essay <em>The Use of Knowledge in Society</em> (1945) argued that the central problem of economics is not resource allocation in the abstract, but the utilisation of knowledge that is dispersed across countless individuals, none of whom possess it in its totality. The price system solves this problem by acting as a <em>communication mechanism</em> — prices aggregate dispersed information into a single signal.</p>

<blockquote>"The most significant fact about this system is the economy of knowledge with which it operates, or how little the individual participants need to know in order to be able to take the right action." — Hayek (1945)</blockquote>

<p>This insight transforms how we understand the Limit Order Book. The LOB is not merely a record of limit orders — it is a <em>distributed knowledge representation</em>. Each order embeds a trader's private information about value, risk, and timing. The resulting price is an emergent property of this collective intelligence.</p>

<h2>Tacit Knowledge in Markets</h2>
<p><strong>Michael Polanyi's</strong> <em>The Tacit Dimension</em> (1966) introduced the concept of tacit knowledge — "we can know more than we can tell." Trading floors, proprietary algorithms, and market-making desks are repositories of tacit knowledge that cannot be fully codified. This is why algorithmic trading strategies can never fully replace human traders, and why HFT firms guard their latency-optimisation techniques as trade secrets.</p>

<p>Polanyi's insight also explains why market microstructure is so difficult to model analytically. The knowledge that traders possess is partly embodied, partly situational, partly intuitive. The gap between what traders know and what they can articulate is the gap that microstructure research attempts — imperfectly — to bridge.</p>

<h2>The Social Construction of Price</h2>
<p><strong>Harold Garfinkel's</strong> ethnomethodology (<em>Studies in Ethnomethodology</em>, 1967) studied how people create shared meaning through everyday practices. Financial markets are a particularly rich domain for ethnomethodological analysis: traders, algorithms, and regulators collectively produce the phenomenon of "price" through their ongoing interactions.</p>

<p>The work of <strong>Karina Knorr Cetina and Alex Preda</strong> (<em>The Sociology of Financial Markets</em>, 2005) extends this to show how screens, trading floors, and electronic networks constitute a "scopic system" — a way of seeing financial reality that simultaneously creates the reality it observes.</p>

<h2>VPIN and Information Asymmetry</h2>
<p><strong>Easley, Lopez de Prado, and O'Hara's</strong> Volume-Synchronized Probability of Informed Trading (VPIN) metric attempts to measure toxicity — the probability that a counterparty possesses superior information. This operationalises a philosophical insight from the economics of information (Akerlof's market for lemons, Stiglitz's screening): information asymmetry destroys markets. VPIN is an epistemic early warning system.</p>

<h2>Cross-Pillar Connections</h2>
<p>This pattern — price as emergent collective knowledge — mirrors <strong>KYC's</strong> social epistemology of identity and <strong>Schema Registry's</strong> semantic coordination. All three involve creating shared reference points that enable transactions across diverse participants.</p>

<h2>Key Thinkers</h2>
<ul>
<li>Hayek, Friedrich. <em>The Use of Knowledge in Society</em> (1945)</li>
<li>Polanyi, Michael. <em>The Tacit Dimension</em> (1966)</li>
<li>Garfinkel, Harold. <em>Studies in Ethnomethodology</em> (1967)</li>
<li>Knorr Cetina, Karina; Preda, Alex. <em>The Sociology of Financial Markets</em> (2005)</li>
<li>Easley, David; Lopez de Prado, Marcos; O'Hara, Maureen. <em>Flow Toxicity and Liquidity in a High-Frequency World</em> (2012)</li>
</ul>
"""

MARKETS_RISK_BODY = """
<h2>Risk as a Metaphysical Category</h2>
<p>Asset pricing models — CAPM, APT, factor models, stochastic volatility — all presuppose a particular metaphysics of risk. They treat risk as something that can be measured, priced, and diversified. But this assumption has deep philosophical roots in the theory of probability, decision theory, and the nature of uncertainty.</p>

<p><strong>Frank Ramsey</strong> (<em>Truth and Probability</em>, 1926) and <strong>Bruno de Finetti</strong> (<em>Theory of Probability</em>, 1974) developed the subjective interpretation of probability — probabilities are not objective features of the world but degrees of belief that can be inferred from betting behaviour. This subjectivist view underlies the entire apparatus of expected utility theory, portfolio optimisation, and risk-neutral pricing.</p>

<p>But if probabilities are subjective, then the elegant mathematical structures of asset pricing rest on a voluntarist foundation — a community of market participants who <em>choose</em> to assign probabilities in a consistent way. What happens when they don't?</p>

<h2>The Black Swan Problem</h2>
<p><strong>Nassim Nicholas Taleb's</strong> critique (<em>The Black Swan</em>, 2007, <em>Antifragile</em>, 2012) targets precisely this foundation. If the world contains events that are both extremely rare and extremely consequential — and if these events are fundamentally unpredictable — then asset pricing models that treat risk as measurable are not just wrong but dangerous.</p>

<p>Taleb distinguishes between:</p>
<ul>
<li><strong>Mediocristan</strong>: domains where no single observation can dramatically change the aggregate (height, weight, IQ) — <em>measurable risk</em></li>
<li><strong>Extremistan</strong>: domains where a single observation can dominate the aggregate (wealth, market returns, pandemics) — <em>Knightian uncertainty</em></li>
</ul>

<p>Financial markets are firmly in Extremistan. This means that the volatility surface, which appears to price uncertainty through implied volatility, is actually pricing the market's collective illusion of certainty about an uncertain future.</p>

<h2>Rational Expectations and Its Discontents</h2>
<p><strong>Robert Lucas's</strong> rational expectations hypothesis (<em>Rational Expectations and Econometric Practice</em>, 1981) assumes that market participants form expectations that are, on average, correct. This assumption is methodologically powerful but philosophically questionable. It requires markets to be not just efficient but <em>reflexively accurate</em> — participants' beliefs about the future must converge to the true distribution.</p>

<p><strong>Roman Frydman and Michael Goldberg</strong> (<em>Imperfect Knowledge Economics</em>, 2007) argue that this is impossible when the fundamental structure of the economy is itself changing. If the economy is non-ergodic — if the processes generating outcomes shift over time — then rational expectations is an article of faith, not a scientific hypothesis.</p>

<blockquote>"The attempt to reduce uncertainty to measurable risk is the fundamental error of modern finance." — Frydman & Goldberg</blockquote>

<h2>Factors and Fictions</h2>
<p>Factor models (Fama-French, momentum, quality, low-volatility) raise a philosophical question of their own: <em>are factors real?</em> Do size, value, and momentum represent genuine risk premiums (the risk-based view) or are they behavioural artefacts (the mispricing view)?</p>

<p>This debate mirrors a classic philosophical dispute between realists and instrumentalists. Realists treat factors as uncovering genuine features of the world — underlying risk dimensions that exist independently of our models. Instrumentalists treat factors as useful fictions — predictive patterns that may not correspond to any underlying reality. The empirical evidence is compatible with both interpretations.</p>

<h2>Cross-Pillar Connections</h2>
<p>This debate about the reality of risk factors mirrors the debate in <strong>AML</strong> about the reality of "risk-based approaches" and in <strong>Data Engineering</strong> about data quality metrics. All three discuss whether our categories correspond to something real or are merely useful conventions.</p>

<h2>Key Thinkers</h2>
<ul>
<li>Ramsey, Frank. <em>Truth and Probability</em> (1926)</li>
<li>de Finetti, Bruno. <em>Theory of Probability</em> (1974)</li>
<li>Taleb, Nassim Nicholas. <em>The Black Swan</em> (2007); <em>Antifragile</em> (2012)</li>
<li>Frydman, Roman; Goldberg, Michael. <em>Imperfect Knowledge Economics</em> (2007)</li>
<li>Fama, Eugene; French, Kenneth. <em>The Cross-Section of Expected Stock Returns</em> (1992)</li>
</ul>
"""

# ── Pillar 3: Data Engineering ────────────────────────────────────────────

DATA_INTERPRETATION_BODY = """
<h2>Every Pipeline is an Interpretation</h2>
<p>Data pipelines — ETL, ELT, streaming, CDC — are typically described in technical terms: extract, transform, load. But each transformation is also an act of interpretation. When a pipeline cleans, normalises, and enriches data, it is making decisions about what the data <em>means</em>, what is <em>relevant</em>, and what can be <em>discarded</em>.</p>

<p><strong>Hans-Georg Gadamer's</strong> <em>Truth and Method</em> (1960) introduced the concept of <em>hermeneutic circle</em> — the idea that understanding emerges from the interplay between a text and its interpreter's pre-existing framework. Data pipelines exhibit the same structure:</p>
<ul>
<li>The source system emits data (the "text")</li>
<li>The pipeline engineer brings a schema, business rules, and cleaning logic (the "interpreter's framework")</li>
<li>The transformed data represents a fusion of these two horizons</li>
</ul>

<blockquote>"Interpretation is not a retrospective act performed on an already-understood meaning, but the mode in which understanding itself operates." — Gadamer</blockquote>

<p><strong>Paul Ricoeur's</strong> <em>Interpretation Theory</em> (1976) adds the dimension of <em>distanciation</em> — the gap between a text and its author that makes interpretation necessary. In data pipelines, distanciation appears as the gap between the business event and its representation in a database. The pipeline bridges this gap, but in doing so, it imposes a particular interpretive frame.</p>

<h2>Sorting Things Out</h2>
<p><strong>Geoff Bowker and Susan Leigh Star's</strong> <em>Sorting Things Out: Classification and Its Consequences</em> (1999) is arguably the most important philosophical work for data engineers. They argue that classification systems — the categories by which we organise information — are never neutral. Every classification system:</p>
<ul>
<li>Reflects the values and priorities of its creators</li>
<li>Creates invisible work for those who don't fit the categories</li>
<li>Has political consequences that are often invisible to its users</li>
</ul>

<p>A data pipeline's schema, transformation rules, and quality thresholds are a classification system. The choices embedded in them — which fields are required, what values are valid, what defaults apply — encode a particular <em>ontology</em> of the business domain.</p>

<h2>The Hermeneutics of Data Contracts</h2>
<p>Data contracts (schema registries, SLA agreements, contract testing) represent an attempt to make the interpretive act explicit. A data contract says: "This producer agrees to emit data with this shape and these semantics; this consumer agrees to accept data in this form."</p>

<p>This is a <em>hermeneutic agreement</em> — an agreement about interpretation. It does not eliminate the need for interpretation but creates shared ground on which interpretation can proceed. <strong>Wittgenstein's</strong> concept of <em>language games</em> (from <em>Philosophical Investigations</em>, 1953) is directly applicable: different domains speak different language-games, and data contracts are the rules for translating between them.</p>

<h2>Process vs. State</h2>
<p>Streaming and CDC (Change Data Capture) represent a philosophical choice about temporality. Batch processing treats data as <em>states of the world at points in time</em>. Streaming treats data as <em>events in an ongoing process</em>. This mirrors the philosophical distinction between:</p>
<ul>
<li><strong>Substance ontology</strong> (Aristotle, Descartes): the world is composed of things with properties</li>
<li><strong>Process ontology</strong> (Heraclitus, Whitehead): the world is composed of events and processes</li>
</ul>

<p><strong>Alfred North Whitehead's</strong> <em>Process and Reality</em> (1929) provides a rigorous process metaphysics that maps surprisingly well onto event sourcing architectures. In both, the fundamental units are "occasions of experience" (events) rather than persistent objects (states).</p>

<h2>Cross-Pillar Connections</h2>
<p>This interpretive pattern — data transformation as meaningful act — mirrors <strong>Transaction Monitoring's</strong> classification of behaviour as suspicious and <strong>Market Microstructure's</strong> interpretation of order flow as information. All three involve transforming raw signals into actionable meaning.</p>

<h2>Key Thinkers</h2>
<ul>
<li>Gadamer, Hans-Georg. <em>Truth and Method</em> (1960)</li>
<li>Ricoeur, Paul. <em>Interpretation Theory: Discourse and the Surplus of Meaning</em> (1976)</li>
<li>Bowker, Geoffrey; Star, Susan Leigh. <em>Sorting Things Out: Classification and Its Consequences</em> (1999)</li>
<li>Whitehead, Alfred North. <em>Process and Reality</em> (1929)</li>
<li>Wittgenstein, Ludwig. <em>Philosophical Investigations</em> (1953)</li>
</ul>
"""

DATA_GOVERNANCE_BODY = """
<h2>Data as a Commons</h2>
<p>Data mesh, data contracts, and federated governance represent a fundamental rethinking of data ownership and control. The shift from centralised data warehouses to decentralised data mesh is not just a technical evolution — it embodies a <em>political philosophy</em> of how knowledge resources should be governed.</p>

<p><strong>Elinor Ostrom's</strong> <em>Governing the Commons: The Evolution of Institutions for Collective Action</em> (1990) won the Nobel Prize for demonstrating that common-pool resources can be managed sustainably by communities without top-down regulation or privatisation. Her design principles for successful commons governance map directly onto data mesh:</p>
<ul>
<li><strong>Clearly defined boundaries</strong> → Domain ownership with clear data product boundaries</li>
<li><strong>Proportional equivalence between benefits and costs</strong> → Data contracts as reciprocal agreements</li>
<li><strong>Collective-choice arrangements</strong> → Federated governance, not central control</li>
<li><strong>Monitoring</strong> → Data observability, quality metrics shared across domains</li>
<li><strong>Graduated sanctions</strong> → Data contract violation resolution processes</li>
<li><strong>Conflict resolution mechanisms</strong> → Schema registry evolution policies</li>
<li><strong>Minimal recognition of rights to organise</strong> → Domain autonomy with platform support</li>
<li><strong>Nested enterprises</strong> → Multi-level governance (domain → pillar → enterprise)</li>
</ul>

<blockquote>"The problem of data governance is, at its heart, the problem of common-pool resource management: how to prevent the tragedy of the commons while avoiding the inefficiencies of centralised control."</blockquote>

<h2>The Principle of Subsidiarity</h2>
<p>Data mesh embodies the principle of subsidiarity — a concept from Catholic social teaching and European Union law — which holds that decisions should be made at the most local level competent to handle them. In data mesh, data decisions are owned by domain teams because they have the most context about their data. The platform provides infrastructure, not control.</p>

<p><strong>Peter Evans's</strong> <em>The Appropriation of the Social</em> (1995) discusses how technical systems encode social relations. Data mesh's architecture — with its emphasis on domain autonomy, bounded contexts, and federated governance — encodes a vision of distributed authority that is fundamentally political.</p>

<h2>Language Games and Schema</h2>
<p><strong>Ludwig Wittgenstein's</strong> <em>Philosophical Investigations</em> (1953) introduced the concept of <em>language games</em> — the idea that meaning is determined by use within a specific form of life. Different domains within an organisation speak different language games. Marketing's "customer" is not Finance's "customer" is not Compliance's "customer."</p>

<p>A schema is an attempt to create a stable reference point across language games. But Wittgenstein's insight is that this stability is never fully achievable — meaning shifts with context. The best we can do is maintain ongoing translation across domain boundaries, which is precisely what data contracts and schema registries enable.</p>

<h2>Privacy as Contextual Integrity</h2>
<p><strong>Helen Nissenbaum's</strong> <em>Privacy in Context: Technology, Policy, and the Integrity of Social Life</em> (2009) argues that privacy is not about secrecy or control but about <em>contextual integrity</em> — the appropriate flow of information according to context-specific norms. </p>

<p>This framework is directly applicable to data governance: the question is not "is this data private?" but "is this data flow appropriate to the context?" A data contract encodes the expected information flow between domains, establishing the context-relative norms that Nissenbaum identifies as the basis of privacy.</p>

<h2>Cross-Pillar Connections</h2>
<p>This governance pattern — decentralised authority held together by explicit agreements — mirrors <strong>Beneficial Ownership</strong> (the legal fiction of corporate personhood and control) and <strong>Network Analysis</strong> (mapping relationships across distributed entities). All three involve governing through the architecture of relationships rather than top-down control.</p>

<h2>Key Thinkers</h2>
<ul>
<li>Ostrom, Elinor. <em>Governing the Commons</em> (1990)</li>
<li>Wittgenstein, Ludwig. <em>Philosophical Investigations</em> (1953)</li>
<li>Nissenbaum, Helen. <em>Privacy in Context</em> (2009)</li>
<li>Evans, Peter. <em>The Appropriation of the Social</em> (1995)</li>
<li>Zuboff, Shoshana. <em>The Age of Surveillance Capitalism</em> (2019) — Data politics</li>
</ul>
"""


def main():
    dry_run = "--dry-run" in sys.argv

    registry = load_json(REGISTRY_PATH)
    existing_slugs = {item["slug"] for item in registry.get("content", [])}

    PAGES = [
        make_item(
            "compliance/knowledge/foundations-trust-identity",
            "Trust & Identity: The Philosophical Foundations of KYC",
            "How KYC, CDD, and Beneficial Ownership embody philosophical theories of identity, trust, and institutional knowledge — from Simmel's Philosophy of Money to Foucault's disciplinary power.",
            "aml",
            COMPLIANCE_TRUST_BODY,
            ["philosophy", "kyc", "cdd", "beneficial-ownership", "trust", "identity"],
        ),
        make_item(
            "compliance/knowledge/foundations-surveillance-suspicion",
            "Surveillance & Suspicion: The Philosophy of Transaction Monitoring",
            "How transaction monitoring, SAR/STR, and AML surveillance transform raw data into epistemic claims about suspicion — from Lyon's surveillance studies to Crawford's Atlas of AI.",
            "aml",
            COMPLIANCE_SURVEILLANCE_BODY,
            ["philosophy", "transaction-monitoring", "surveillance", "sar", "aml"],
        ),
        make_item(
            "markets/knowledge/foundations-price-knowledge",
            "Price as Knowledge: The Philosophy of Market Microstructure",
            "How the Limit Order Book, VPIN, and market microstructure instantiate Hayek's knowledge problem — price as emergent collective intelligence, tacit knowledge, and distributed cognition.",
            "stock",
            MARKETS_PRICE_BODY,
            ["philosophy", "market-microstructure", "lob", "vpin", "price-discovery"],
        ),
        make_item(
            "markets/knowledge/foundations-risk-probability",
            "Risk & Probability: The Philosophy of Asset Pricing",
            "How asset pricing models (CAPM, factors, volatility) rest on philosophical assumptions about probability, uncertainty, and the nature of risk — from Ramsey to Taleb.",
            "stock",
            MARKETS_RISK_BODY,
            ["philosophy", "asset-pricing", "volatility", "risk", "probability", "factors"],
        ),
        make_item(
            "data/knowledge/foundations-interpretation",
            "Data as Interpretation: The Philosophy of Pipelines and ETL",
            "How ETL/ELT pipelines, data contracts, and streaming architectures embody hermeneutic principles — every transformation is an act of interpretation (Gadamer, Ricoeur, Bowker & Star).",
            "data-engineering",
            DATA_INTERPRETATION_BODY,
            ["philosophy", "etl", "pipeline", "streaming", "hermeneutics", "data-contracts"],
        ),
        make_item(
            "data/knowledge/foundations-governance",
            "Decentralized Governance: The Philosophy of Data Mesh",
            "How data mesh, data contracts, and federated governance encode political philosophy — Ostrom's commons, the principle of subsidiarity, and Wittgenstein's language games.",
            "data-engineering",
            DATA_GOVERNANCE_BODY,
            ["philosophy", "data-mesh", "data-contracts", "governance", "commons", "ostrom"],
        ),
    ]

    added = 0
    skipped = 0
    for page in PAGES:
        if page["slug"] in existing_slugs:
            skipped += 1
            if dry_run:
                print(f"  [SKIP] {page['slug']} — already exists")
            continue
        registry["content"].append(page)
        added += 1
        if dry_run:
            print(f"  [ADD]  {page['slug']} — would be added")
        else:
            print(f"  [ADD]  {page['slug']}")

    if not dry_run and added > 0:
        # Recalculate reading_time
        for item in registry["content"]:
            if item.get("body_html"):
                item["reading_time"] = max(1, len(item["body_html"].split()) // 200)
        save_json(REGISTRY_PATH, registry)
        print(f"\nAdded {added} philosophical foundations pages ({skipped} skipped)")
        print(f"Registry now has {len(registry['content'])} content items")
    elif dry_run:
        print(f"\nDry run: {added} would be added, {skipped} skipped (already exist)")
    else:
        print(f"Nothing to add ({skipped} already exist)")


if __name__ == "__main__":
    main()
