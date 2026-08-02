#!/usr/bin/env python3
"""Generate cross-pillar "synthesis essay" knowledge pages.

Captures the research synthesis on the evolution of language and law (Savigny,
Hart), the law–markets–data intersection, systemic risk literature (Lessig,
Hildebrandt, Zuboff, Schwarcz), future risks (algorithmic cascades, loss of
contestability, epistemic crisis, digital neofeudalism), and computational
constitutionalism — written as analytical knowledge essays and anchored to the
site's three pillars.

Each essay uses the advanced-difficulty voice, h2 sections (rendered as
collapsible prose sections at build time), Bloom questions at the
analyze/evaluate/create levels, and links into the ontology concepts seeded by
`scripts/seed_synthesis_concepts.py`.

Usage:
    python3 scripts/generate_synthesis_essays.py           # add pages to registry
    python3 scripts/generate_synthesis_essays.py --dry-run # preview without writing
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"

NOW = datetime.now(timezone.utc).isoformat()
TODAY_STR = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_item(
    slug: str,
    title: str,
    description: str,
    pillar: str,
    body_html: str,
    tags: list[str],
    knowledge_category: str,
    bloom_questions: list[dict],
) -> dict:
    return {
        "slug": slug,
        "language": "en",
        "title": title,
        "description": description,
        "body_html": body_html,
        "content_type": "knowledge",
        "knowledge_category": knowledge_category,
        "category": knowledge_category,
        "pillar": pillar,
        "tags": tags,
        "difficulty": "advanced",
        "bloom_questions": bloom_questions,
        "flashcards": [],
        "source_breakdown": {"synthesized": 1},
        "signals": {"avg_sqi": 0.9, "count": 1},
        "quality_metrics": {"density": 0.9, "code_ratio": 0.05},
        "sqi": 0.9,
        "reading_time": max(2, len(body_html.split()) // 200),
        "deprecated": False,
        "created_at": NOW,
        "updated_at": NOW,
        "enriched": True,
        "enriched_at": NOW,
        "date_str": TODAY_STR,
        "author": "AcaciaFund",
    }


def bloom(level: str, question: str) -> dict:
    return {"level": level, "question": question}


# ── Essay 1: The Law–Markets–Data Triangle ──────────────────────────────────

TRIANGLE_BODY = """
<p>Law, markets and data are usually studied as separate disciplines. This essay argues they are
<strong>three layers of one governance system</strong>, each running at a different speed. Once you see
the system, a great deal that looks like confusion — regulatory lag, enforcement asymmetry, flash crashes,
surveillance — becomes a predictable consequence of clocks that are out of sync.</p>

<h2>Three layers, three speeds</h2>
<p>Think of any regulated economic act — a payment, a trade, a lending decision — as an event that passes
through three layers:</p>
<ul>
<li><strong>Law</strong> is the <em>governance protocol</em>: rules about who may act, under what conditions,
with what evidence, and at whose risk. Its native unit of time is years. A statute takes months to draft and
years to be interpreted into a settled meaning. Even fast-track regulation moves in quarters.</li>
<li><strong>Markets and money</strong> are the <em>incentive layer</em>: prices, contracts, and market
mechanisms that coordinate behaviour through rewards and penalties. Their native unit of time is seconds to
quarters. A price reprices in microseconds; an earnings cycle takes a quarter.</li>
<li><strong>Data</strong> is the <em>information substrate</em>: the records, signals, and models through
which both law and markets observe reality. Its native unit of time is real time — a transaction is logged in
milliseconds, a market feed in microseconds.</li>
</ul>
<p>These are not three industries. They are three layers of one system, and each layer can only act on the
evidence produced by the layer below it.</p>

<h2>The temporal mismatch</h2>
<p>The same act is therefore evaluated at three speeds simultaneously:</p>
<ul>
<li><strong>Data records it in milliseconds.</strong> The event exists as a timestamped fact almost instantly.</li>
<li><strong>Markets price it in seconds.</strong> The event changes incentives and is reflected in prices while
it is still fresh.</li>
<li><strong>Law judges it in years.</strong> The event is finally characterised — lawful or not, sanctioned or
protected — long after it has been recorded and priced.</li>
</ul>
<p>This mismatch is the <em>regulatory lag</em> that the other essays in this series explore. It is structural,
not accidental: legislation is slow because legitimacy requires deliberation, and deliberation requires time.
But the cost of that slowness is an <strong>enforcement asymmetry</strong> — fast actors exploit the window in
which novel conduct is not yet characterised by law, and slow institutions can only react to the past.</p>

<h2>Feedback loops, not one-way flows</h2>
<p>Viewing the triangle as a cybernetic system (in Wiener's sense) reveals that the layers influence each
other through feedback, not just in a single direction:</p>
<ul>
<li><strong>Law → Markets:</strong> a new rule changes incentives, which changes prices and behaviour.</li>
<li><strong>Markets → Data:</strong> repricing produces new data, new volumes, new patterns.</li>
<li><strong>Data → Law:</strong> revealed patterns (money laundering typologies, market abuse, data breaches)
feed back into legislation and supervision.</li>
</ul>
<p>When a layer is missing or broken, the whole loop degrades. Without good data, both markets and law are
blind. Without working markets, prices stop carrying information. Without legitimate law, neither layer has a
stable frame to operate in.</p>

<h2>Why the triangle matters here</h2>
<p>This platform is organised around the same three layers. The Compliance pillar is the law layer — AML and
regulatory rule frameworks. The Markets pillar is the incentive layer — market microstructure, volatility,
trading. The Data Engineering pillar is the information substrate — pipelines, schemas, data contracts,
governance. Reading the site as one system, rather than three silos, is the point of the cross-pillar
synthesis.</p>
<p>The practical lesson: when you diagnose a problem in one pillar, check the other two. A compliance failure
is frequently a data problem wearing a legal costume. A market failure is frequently a data problem wearing a
microstructure costume. The triangle is the shared skeleton underneath.</p>
"""

# ── Essay 2: Law & Language ─────────────────────────────────────────────────

LANGUAGE_BODY = """
<p>Law is a language technology. Rules are written in words, interpreted through words, and enforced because
words can bind. This essay traces the long argument — from Savigny to Hart — that law evolves the way
language does, and draws out what that means for modern compliance systems that must turn legislative
sentences into executable predicates.</p>

<h2>Savigny and the historical school</h2>
<p>Friedrich Carl von Savigny, writing at the turn of the nineteenth century, rejected the idea that law was a
timeless, deductive system that a legislature could simply invent. In <em>On the Vocation of Our Age for
Legislation and Jurisprudence</em> (1814) he argued that law grows organically out of a people's life — its
<em>Volksgeist</em>, its spirit — the same way language does. A language cannot be designed by committee and
decreed into being; it lives in speakers, changes with usage, and dies when no one speaks it.</p>
<p>Law, Savigny held, is the same: it is not a closed formal system but a living practice carried by
jurists and citizens. The insight that matters for us is not romantic nationalism but the <strong>analogy
itself</strong> — rules, like words, acquire meaning through use, drift with time, and resist being fixed by
flat.</p>

<h2>Hart: rules about rules, and open texture</h2>
<p>H. L. A. Hart's <em>The Concept of Law</em> (1961) gives the analogy a precise shape. Law, for Hart, is a
union of two kinds of rule:</p>
<ul>
<li><strong>Primary rules</strong> impose obligations — do not launder money, do not mislead investors, do not
misreport.</li>
<li><strong>Secondary rules</strong> are rules about rules — how rules are recognised (a constitution, a
statute book), how they are changed (legislation), and how they are adjudicated (courts).</li>
</ul>
<p>Hart's crucial claim for systems design is <em>open texture</em>: natural-language terms always have a
"penumbra" of uncertainty. Words like "suspicious", "reasonable", "beneficial", and "risk" have a settled core
and a hazy fringe. At the fringe, judges exercise discretion. Open texture is not a defect of language; it is
what lets law adapt to cases the legislator never imagined. But it is exactly the property that makes
natural-language rules hard to execute mechanically.</p>

<h2>The translation problem in compliance</h2>
<p>Every AML and compliance rule faces the same journey: legislative sentence → regulator guidance →
internal policy → executable predicate (a Boolean filter, a threshold, a machine-learning score). Each step of
translation is a lossy compression of meaning.</p>
<ul>
<li>"Suspicious transaction" becomes a pattern rule about structuring around reporting thresholds.</li>
<li>"Beneficial ownership" becomes a lookup across a corporate register with a <em>cutoff</em> at a percentage
ownership stake.</li>
<li>"Reasonable steps" becomes a documented due-diligence checklist.</li>
</ul>
<p>The gap between what the words mean and what the predicate tests is where compliance risk actually lives.
A model that exactly follows the predicate can still be entirely unfaithful to the rule — and a rule
faithfully applied can still be wrong in open-textured cases. Understanding this gap is the difference between
a compliance function that mechanically checks boxes and one that reasons about whether the boxes mean what
the law says.</p>

<h2>Semantic drift and the linguistic arms race</h2>
<p>Words change meaning as the world changes, and law must chase them. "Money" once meant notes and coin; it
now includes crypto-assets, stablecoins, and tokenised instruments. "Identity" once meant a paper document; it
now means a verified credential in an ecosystem. Regulators respond through guidance, interpretive notes, and
amendment — a <em>linguistic arms race</em> in which the regulated community and the regulator continuously
renegotiate what the words mean.</p>
<p>Two modern movements respond directly to this. The <strong>plain-language movement</strong> tries to shrink
open texture by drafting rules a citizen can read. The <strong>Rules-as-Code / legislation-as-code
experiments</strong> (in New Zealand, Canada, and elsewhere) try to draft law in machine-executable form from
the start, so that the translation loss described above shrinks to zero.</p>

<h2>What a schema has to do with a statute</h2>
<p>From a data-engineering perspective, the analogy is almost literal. A schema is a legislature for a
database: it fixes the shape of the words (fields, types, allowed values) and the rules of change (versioning,
migration, breaking-change review). A data contract between two systems is a treaty about meaning. The same
open texture Hart found in statutes appears in schemas whenever a field is vaguely defined or a contract is
silent on semantics. The discipline of governing a database's vocabulary is, in miniature, the discipline of
governing a legal system's vocabulary. That is why this essay belongs in the law–language–data story: the
problems of meaning are shared, and so are the tools.</p>
"""

# ── Essay 3: Compliance-by-Design ───────────────────────────────────────────

DESIGN_BODY = """
<p>Compliance is increasingly an architecture problem, not a policy problem. If a rule must be enforced, the
strongest way to enforce it is to make the compliant path the only structurally possible path. This essay
lays out compliance-by-design: rules as versioned code, data contracts as legal interfaces, lineage as
evidence, and circuit breakers as the last line of defence.</p>

<h2>From inspection to design</h2>
<p>There are two ways to achieve compliance. <strong>Ex-post inspection</strong> lets behaviour happen and
then checks whether it broke a rule — audits, reviews, fines. It is reactive, sampled, and always one step
behind. <strong>Ex-ante design</strong> embeds the rule in the machinery so that violating behaviour is
difficult or impossible to produce in the first place — controls, permission systems, schema constraints,
real-time screening.</p>
<p>Lessig's famous claim that "code is law" cuts both ways here: if software architecture regulates behaviour
as effectively as statutes, then architecture is also where compliance should be built. Design is not a
softening of law — it is law's most reliable enforcement mechanism.</p>

<h2>Rules as versioned artifacts</h2>
<p>The core move of compliance-by-design is to treat a rule as an <strong>artifact</strong>: a versioned,
tested, deployable unit, managed the way software is managed. This is <em>policy-as-code</em> — the pattern
familiar from Open Policy Agent and Kubernetes admission controllers, applied to compliance domains.</p>
<ul>
<li><strong>Versioning:</strong> every rule change is a commit with an author, a timestamp, and a rationale.
The rule history is the legislative record.</li>
<li><strong>Testing:</strong> each rule carries fixtures — the cases it must catch and the cases it must not.
A rule that cannot be tested cannot be trusted.</li>
<li><strong>Auditability:</strong> because the rule is executable, you can prove which version was in force at
any moment, and exactly what it did.</li>
</ul>
<p>In this framing, <strong>Git is a legislature</strong>: it provides recognition, change, and a traceable
record of every decision — Hart's secondary rules, implemented in a version-control system.</p>

<h2>Data contracts as legal interfaces</h2>
<p>A data contract is a binding agreement between two systems about the shape, semantics, and provenance of
the data they exchange. It is the data-engineering analogue of a treaty: it fixes what words mean, what is
required, and what happens when either side changes.</p>
<p>For compliance-by-design, contracts are where legal meaning becomes machine-checkable. When a contract says
a field "must be verified", that is a legal obligation encoded as a schema constraint. When lineage records
every transformation a value passed through, that is an evidentiary trail a regulator can audit. Contracts
give the law layer a reliable view of the information substrate — and without that view, the law layer is
blind.</p>

<h2>Evidence as lineage</h2>
<p>Enforcement depends on evidence, and in a data-driven system evidence is provenance. Data lineage — who
produced a value, from what inputs, through which transformations — converts an assertion ("we screened this
customer") into a claim that can be verified end to end.</p>
<p>This is why <em>observability is a compliance capability</em>: a pipeline you cannot trace is a compliance
process you cannot defend. The same logs that debug an outage document the case file.</p>

<h2>Circuit breakers and the human residue</h2>
<p>Even the best design fails, so the system needs circuit breakers: kill switches that halt or quarantine a
process when it crosses a threshold — a runaway model, a suspicious burst of activity, a data feed gone stale.
Circuit breakers are the admission that architecture cannot foresee everything, and that the system must fail
toward caution rather than toward exposure.</p>
<p>Equally important is the <strong>human residue</strong>. Not everything should be automated. Open texture
(Hart), contestability, and discretion all argue for keeping a human review lane in the loop — especially
for decisions that affect a person's access to services. Compliance-by-design is not automation-at-all-costs;
it is architecture that decides <em>which</em> decisions are safe to automate and <em>which</em> must remain
contestable by a person.</p>
"""

# ── Essay 4: Computational Constitutionalism ─────────────────────────────────

CONSTITUTIONAL_BODY = """
<p>When code becomes law, constitutional questions migrate into systems architecture. This essay assembles
the argument — Lessig, Hildebrandt, Zuboff, Schwarcz — and names the four next-generation risks that
follow, before sketching the response: computational constitutionalism.</p>

<h2>Code is law</h2>
<p>Lawrence Lessig's <em>Code and Other Laws of Cyberspace</em> (1999) argued that the architecture of
software regulates behaviour more effectively than statutes ever can. A law says "you may not"; a protocol
makes it so you <em>cannot</em>. When a platform's code determines who can speak, trade, or be seen, the
platform's engineering decisions have the force of law — without the legitimacy, accountability, or checks of
law. Private code, Lessig showed, is a public question.</p>

<h2>Legal protection by design</h2>
<p>Mireille Hildebrandt extends the point into a demand: if the technological environment regulates us, then
law must be capable of protecting us <em>from within that environment</em>. "Legal protection by design" means
the constraints of law — due process, contestability, transparency — must be built into the machines that
apply it. Law cannot remain a layer sitting on top of code; it has to be woven into the code itself. This is
the philosophical warrant for the compliance-by-design essay in this series.</p>

<h2>Surveillance capitalism and systemic risk</h2>
<p>Two further literatures define the threat model. Shoshana Zuboff's <em>The Age of Surveillance
Capitalism</em> (2019) describes how data becomes <em>behavioral surplus</em>: extracted from users, refined
into prediction, and sold back as control. The asymmetry — institutions that know vastly more about you than
you can know about them — is a structural feature, not a bug, and it concentrates power wherever data
concentrates.</p>
<p>Steven Schwarcz's work on systemic risk supplies the failure mechanics: in a tightly interconnected system,
the failure of one node propagates through linkages until a single default threatens the whole. His analysis
predates the algorithmic era but generalises cleanly to it — with one change: the interconnections are now
faster, more correlated, and partly invisible because they live in code and shared data feeds.</p>

<h2>Four next-generation risks</h2>
<p>Putting the three literatures together yields four risks that no longer belong to a single pillar:</p>
<ol>
<li><strong>Algorithmic cascades.</strong> Correlated automated strategies amplify a shock through feedback
loops — herd-style models sharing the same data feeds and reacting in microseconds. Circuit breakers designed
for human trading floors cannot stop a stampede that outruns human reaction time. The 2010 Flash Crash is the
canonical near-miss: ~$1 trillion of value vanishing and returning in minutes because machines amplified a
large order into a cascade.</li>
<li><strong>Loss of contestability.</strong> When decisions are made by opaque models from one-way data flows,
affected people lose any meaningful avenue of appeal. A customer silently placed on a high-risk list, with no
explanation and no effective review, is a person excluded from the system without due process. GDPR Article 22
and the EU AI Act's human-oversight duties are early, partial attempts to restore the door of appeal.</li>
<li><strong>Epistemic crisis of ground truth.</strong> Both markets and law act on the information substrate —
and if that substrate is polluted, everything above it is unreliable. Synthetic data, adversarial data, model
collapse (models trained on their own output losing fidelity), and coordinated disinformation all attack the
assumption that the substrate describes reality. "Who verifies the verifiers?" becomes an architectural
question: verification itself must be designed, evidenced, and itself verified.</li>
<li><strong>Digital neofeudalism.</strong> When a handful of platforms own the identity graph, the payment
rails, and the rules of participation, terms of service function as constitutional law — drafted by one
party, enforced by that party, with no separation of powers and only nominal exit. Data plays the role of the
land: the fixed, concentrated resource that determines who can participate and on what terms.</li>
</ol>

<h2>The response: computational constitutionalism</h2>
<p>Computational constitutionalism is the refusal to accept any of these as inevitable. It translates
constitutional values into architecture:</p>
<ul>
<li><strong>Due process</strong> becomes auditable decision trails, versioned rule histories, and a right to
review.</li>
<li><strong>Transparency</strong> becomes lineage, explainability hooks, and open rule artifacts.</li>
<li><strong>Contestability</strong> becomes a designed appeals lane that a person can actually reach.</li>
<li><strong>Accountability</strong> becomes the coupling of every automated decision to an identifiable rule
version and an identifiable human or institution.</li>
</ul>
<p>RegTech and SupTech — with auditability built in — are the institutional instruments; the ontology and
synthesis machinery of a site like this one is the intellectual instrument. The three pillars are, in the end,
three fronts of one response: AML as due process, market design as incentive discipline, and data engineering
as the substrate of accountability. The constitutional question is whether the substrate can be made to serve
the constitution rather than the other way around.</p>
"""


def main():
    dry_run = "--dry-run" in sys.argv

    registry = load_json(REGISTRY_PATH)
    existing_slugs = {item["slug"] for item in registry.get("content", [])}

    PAGES = [
        make_item(
            "data/knowledge/law-markets-data-triangle",
            "The Law–Markets–Data Triangle: Three Speeds, One System",
            "Law, markets, and data as three layers of one governance system — a governance protocol running in years, an incentive layer running in seconds, and an information substrate running in real time. How the temporal mismatch between them produces regulatory lag, enforcement asymmetry, and feedback loops.",
            "data-engineering",
            TRIANGLE_BODY,
            ["cross-pillar", "synthesis", "law-markets-data", "systems-theory", "regulatory-lag", "governance"],
            "foundations",
            [
                bloom("understand", "In your own words, what does each of the three layers govern, and at what unit of time?"),
                bloom("analyze", "Pick a regulated act (a payment, a trade, a data breach) and trace it through all three layers, noting where each layer reacts and how fast."),
                bloom("evaluate", "Is regulatory lag a bug to be fixed or a structural price of legitimacy? Defend your position."),
                bloom("create", "Propose one mechanism that could shorten the law layer's response time without sacrificing due process."),
            ],
        ),
        make_item(
            "compliance/knowledge/law-and-language",
            "Law & Language: How Rules Learn to Mean",
            "From Savigny's historical school to Hart's open texture: how law evolves the way language does, why natural-language rules always carry a penumbra of uncertainty, and what that means for turning legislative sentences into executable compliance predicates.",
            "aml",
            LANGUAGE_BODY,
            ["legal-philosophy", "cross-pillar", "synthesis", "open-texture", "rules-as-code", "semantic-drift"],
            "foundations",
            [
                bloom("understand", "Explain Hart's distinction between primary and secondary rules, and where open texture comes from."),
                bloom("analyze", "Take one open-textured term in AML (e.g. 'suspicious' or 'beneficial ownership') and trace its translation from statute to executable predicate, identifying where meaning is lost."),
                bloom("evaluate", "Should legislation be drafted in machine-executable form from the start? Weigh the benefits against the risks of fixing open texture too early."),
                bloom("create", "Design a rule artifact that captures the meaning of an open-textured legal term better than a naive threshold does."),
            ],
        ),
        make_item(
            "data/knowledge/compliance-by-design",
            "Compliance-by-Design: When the Rulebook Lives in the Pipeline",
            "Why compliance is becoming an architecture problem: rules as versioned code, data contracts as legal interfaces, lineage as evidence, and circuit breakers — with a deliberate human residue for contestability.",
            "data-engineering",
            DESIGN_BODY,
            ["compliance-by-design", "policy-as-code", "cross-pillar", "synthesis", "data-contracts", "data-governance"],
            "architecture",
            [
                bloom("understand", "What is the difference between ex-post inspection and ex-ante design as compliance strategies?"),
                bloom("analyze", "Compare a sanctions-screening rule enforced at the database level versus one applied by a downstream reviewer. What changes in risk and evidence?"),
                bloom("evaluate", "Where must a human remain in the loop in an automated compliance system, and why?"),
                bloom("create", "Sketch a policy-as-code rule for a KYC requirement, including the fixtures that would test it."),
            ],
        ),
        make_item(
            "compliance/knowledge/computational-constitutionalism",
            "From Analog Rule to Computational Constitutionalism",
            "Lessig, Hildebrandt, Zuboff, and Schwarcz, assembled: why code is law, how legal protection by design works, and the four next-generation risks — algorithmic cascades, loss of contestability, epistemic crisis, and digital neofeudalism — plus the architectural response.",
            "aml",
            CONSTITUTIONAL_BODY,
            ["computational-constitutionalism", "systemic-risk", "cross-pillar", "synthesis", "surveillance-capitalism", "suptech"],
            "regulations",
            [
                bloom("understand", "What does 'code is law' mean, and why does it make private engineering a public concern?"),
                bloom("analyze", "Trace one of the four next-generation risks (cascade, contestability, epistemic crisis, neofeudalism) through all three layers of the law–markets–data triangle."),
                bloom("evaluate", "Which of the four risks is most urgent, and which is most tractable? Justify your ranking."),
                bloom("create", "Propose a 'due process in code' requirement — a concrete, auditable mechanism — and specify how it would be verified."),
            ],
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
        for item in registry["content"]:
            if item.get("body_html"):
                item["reading_time"] = max(2, len(item["body_html"].split()) // 200)
        save_json(REGISTRY_PATH, registry)
        print(f"\nAdded {added} synthesis essays ({skipped} skipped)")
        print(f"Registry now has {len(registry['content'])} content items")
    elif dry_run:
        print(f"\nDry run: {added} would be added, {skipped} skipped (already exist)")
    else:
        print(f"Nothing to add ({skipped} already exist)")


if __name__ == "__main__":
    main()
