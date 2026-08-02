#!/usr/bin/env python3
"""Seed ontology concepts and relations from the law–markets–data synthesis.

Adds the cross-pillar concepts introduced by the research synthesis on the
evolution of language and law (Savigny, Hart), the law–markets–data
intersection, systemic risk literature (Lessig, Hildebrandt, Zuboff, Schwarcz),
and computational constitutionalism.

Idempotent: existing concepts have aliases merged and are otherwise left intact.

Usage:
    python3 scripts/seed_synthesis_concepts.py          # add concepts + relations
    python3 scripts/seed_synthesis_concepts.py --dry-run # preview without writing
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"

sys.path.insert(0, str(PROJECT_ROOT))

from core.ontology import Concept, OntologyManager, Relation  # noqa: E402


def make_concept(
    *,
    cid: str,
    label: str,
    description: str,
    category: str,
    pillar: str = "cross-pillar",
    aliases: list[str] | None = None,
    lineage: list[str] | None = None,
    epistemic: str,
    normative: str,
    ontology_commitment: str,
    temporal: str,
    uncertainty: str,
    governance: str,
    semantic_contract: str,
    sources: list[str] | None = None,
    analogs: list[str] | None = None,
    eli5: str,
    analogy: str,
    example: str,
    gap_questions: list[str],
    teach_back: str,
) -> Concept:
    return Concept(
        id=cid,
        label=label,
        description=description,
        pillar=pillar,
        category=category,
        aliases=aliases or [],
        source_inspiration="curated",
        confidence_score=0.85,
        philosophical_lineage=lineage or ["legal_philosophy", "systems_theory"],
        epistemic_status=epistemic,
        normative_basis=normative,
        ontological_commitment=ontology_commitment,
        temporal_ontology=temporal,
        uncertainty_class=uncertainty,
        governance_model=governance,
        semantic_contract_type=semantic_contract,
        philosophical_sources=sources or [],
        cross_pillar_analogs=analogs or [],
        eli5_explanation=eli5,
        analogy=analogy,
        concrete_example=example,
        gap_questions=gap_questions,
        teach_back_prompt=teach_back,
        feynman_difficulty=3,
        explanation_quality=0.8,
    )


CONCEPTS = [
    make_concept(
        cid="law-markets-data-triangle",
        label="Law–Markets–Data Triangle",
        description=(
            "A cross-pillar framework describing law, markets/money, and data as three "
            "layers of one governance system running at different speeds: law is the "
            "governance protocol (years), markets the incentive layer (seconds to "
            "quarters), data the information substrate (real-time). Their temporal "
            "mismatch drives both regulatory lag and enforcement asymmetry."
        ),
        category="foundations",
        aliases=["three pillars", "law markets data"],
        lineage=["systems_theory", "social_epistemology", "legal_philosophy"],
        epistemic="constitutive",
        normative="contractarian",
        ontology_commitment="processual",
        temporal="processual",
        uncertainty="ambiguity",
        governance="polycentric",
        semantic_contract="coordinating",
        sources=[
            "Hildebrandt, Mireille. Law for Computer Scientists (2020)",
            "Lessig, Lawrence. Code and Other Laws of Cyberspace (1999)",
        ],
        analogs=["aml-regulatory-framework", "market-microstructure", "data-governance"],
        eli5=(
            "Picture a city where three clocks run at different speeds. One clock (law) "
            "ticks once a year, another (the market) every few seconds, and a third "
            "(data) thousands of times a second. They all describe the same city — you "
            "just have to read all three to understand it."
        ),
        analogy=(
            "Like a thermostat in a room: temperature readings (data) arrive instantly, "
            "the heating contract (market) reacts in minutes, and the building code "
            "(law) that set the range updates only every few years."
        ),
        example=(
            "A suspicious transfer: recorded in a database in milliseconds, repriced by "
            "markets in seconds, screened by AML filters in minutes, and judged in "
            "court only years later. Each layer is doing its job — at its own speed."
        ),
        gap_questions=[
            "What does each of the three layers govern, and at what timescale?",
            "What breaks when one layer runs far faster than the others?",
            "How do the three pillars of this site map onto the triangle?",
        ],
        teach_back=(
            "Explain the triangle to a colleague: name each layer, its unit of time, "
            "and one example of a feedback loop between layers."
        ),
    ),
    make_concept(
        cid="computational-constitutionalism",
        label="Computational Constitutionalism",
        description=(
            "The project of translating constitutional values — due process, "
            "transparency, contestability, accountability, separation of powers — into "
            "the architecture of software and data systems. Responds to Lessig's claim "
            "that 'code is law' by demanding that code itself be subject to "
            "constitutional constraints, and to Hildebrandt's demand for legal "
            "protection by design."
        ),
        category="regulations",
        aliases=["code is law", "rules as code", "legal protection by design"],
        lineage=["legal_philosophy", "technology_philosophy", "republicanism"],
        epistemic="regulatory",
        normative="kantian_duty",
        ontology_commitment="constructivist",
        temporal="event_based",
        uncertainty="ignorance",
        governance="constitutional",
        semantic_contract="constitutive",
        sources=[
            "Lessig, Lawrence. Code and Other Laws of Cyberspace (1999)",
            "Hildebrandt, Mireille. Smart Technologies and the End(s) of Law (2015)",
            "Zuboff, Shoshana. The Age of Surveillance Capitalism (2019)",
        ],
        analogs=["regtech", "ai-aml-surveillance", "data-governance"],
        eli5=(
            "If a city's laws are rewritten in a language only robots read, then the "
            "robots need built-in brakes and inspection windows — otherwise no human "
            "can ever say 'that rule is unfair' and be heard."
        ),
        analogy=(
            "A constitution is a lock on the government's toolbox. Computational "
            "constitutionalism asks: what locks belong on the algorithms' toolbox, "
            "and who keeps the keys?"
        ),
        example=(
            "The EU AI Act's high-risk requirements and GDPR Article 22 (right not to "
            "be subject to automated decision-making) are early attempts to impose "
            "constitutional-style constraints on code."
        ),
        gap_questions=[
            "What does 'code is law' mean, and why does it make private code a public concern?",
            "Which constitutional value is hardest to encode: due process, contestability, or transparency?",
            "How would you audit an algorithm for compliance with a constitution?",
        ],
        teach_back=(
            "Teach the idea: laws used to be written for humans; now they are "
            "increasingly executed by machines — so the constraints must live inside "
            "the machine too."
        ),
    ),
    make_concept(
        cid="compliance-by-design",
        label="Compliance-by-Design",
        description=(
            "The practice of embedding legal and regulatory rules directly into the "
            "architecture of data pipelines and software systems — versioned "
            "rule artifacts, data contracts as legal interfaces, lineage as evidence, "
            "and circuit breakers — so that compliant behaviour is structurally "
            "possible rather than inspected after the fact."
        ),
        category="regtech",
        aliases=["policy as code", "regulation by design", "regtech architecture"],
        lineage=["technology_philosophy", "pragmatism"],
        epistemic="instrumental",
        normative="pragmatic",
        ontology_commitment="constructivist",
        temporal="state_based",
        uncertainty="measurable",
        governance="algorithmic",
        semantic_contract="coordinating",
        sources=[
            "Lessig, Lawrence. Code and Other Laws of Cyberspace (1999)",
            "Kubernetes / Open Policy Agent (OPA) policy-as-code patterns",
        ],
        analogs=["data-governance", "aml-data-governance", "data-contracts"],
        eli5=(
            "Instead of baking a cake and then checking it against the recipe, "
            "compliance-by-design bakes the recipe into the oven so a wrong step is "
            "hard to make in the first place."
        ),
        analogy=(
            "A playground with a fence: the fence (design) prevents wandering into the "
            "street, so you don't need someone to run after every child (inspection)."
        ),
        example=(
            "Encoding a sanctions list as versioned rules evaluated inside a payment "
            "pipeline (policy-as-code), so a frozen entity can never slip through a "
            "screen — the rule is part of the path the transaction must take."
        ),
        gap_questions=[
            "Why is ex-ante design stronger than ex-post inspection?",
            "What must be true of rule artifacts for compliance-by-design to be auditable?",
            "Where should humans remain in the loop, and why?",
        ],
        teach_back=(
            "Explain how a rule becomes an artifact in a pipeline, from legislative "
            "text to executable predicate, and how lineage proves what was done."
        ),
    ),
    make_concept(
        cid="regulatory-lag",
        label="Regulatory Lag",
        description=(
            "The temporal gap between the speed of data (real-time), markets "
            "(seconds), and law (months to years). Because statutes move slowest, "
            "rules are always catching up to the behaviour they regulate, producing "
            "enforcement asymmetry and a window in which novel conduct is unregulated."
        ),
        category="regulations",
        aliases=["legal lag", "pace lag", "legislative lag"],
        lineage=["legal_philosophy", "social_epistemology"],
        epistemic="regulatory",
        normative="utilitarian",
        ontology_commitment="processual",
        temporal="processual",
        uncertainty="ambiguity",
        governance="hierarchical",
        semantic_contract="descriptive",
        sources=[
            "Hart, H. L. A. The Concept of Law (1961)",
            "Savigny, Friedrich Carl von. On the Vocation of Our Age for Legislation and Jurisprudence (1814)",
        ],
        analogs=["aml-regulatory-framework", "global-sanctions", "aml-risk-scoring"],
        eli5=(
            "If rules moved at the speed of a garden snail and the things they govern "
            "moved at the speed of a race car, the snail would always be looking at "
            "where the car used to be. Regulatory lag is that snail."
        ),
        analogy=(
            "Updating a map of a river after the river has already changed course: by "
            "the time the new map prints, the channel has moved again."
        ),
        example=(
            "Crypto assets were traded for years before most jurisdictions defined "
            "them in law; the definition, when it arrived, was written about the "
            "technology of the previous decade."
        ),
        gap_questions=[
            "What is the unit of time for each of the three layers of the triangle?",
            "Why does lag create arbitrage opportunities for novel conduct?",
            "Which mechanisms shorten regulatory lag today?",
        ],
        teach_back=(
            "Explain why 'the law moves slowly' is not just a complaint but a structural "
            "feature of the law–markets–data triangle."
        ),
    ),
    make_concept(
        cid="algorithmic-cascade",
        label="Algorithmic Cascade",
        description=(
            "A failure mode in which correlated automated strategies amplify a shock "
            "through feedback loops — herd-style models, shared data feeds, and "
            "reflexive price reactions — producing flash crashes and system-wide "
            "stress faster than any human or slow-moving rule can respond. The "
            "algorithmic extension of Schwarcz's systemic risk."
        ),
        category="risk-assessment",
        aliases=["algorithmic systemic risk", "cascade failure", "flash crash"],
        lineage=["systems_theory", "complexity_theory"],
        epistemic="instrumental",
        normative="utilitarian",
        ontology_commitment="processual",
        temporal="event_based",
        uncertainty="knightian",
        governance="algorithmic",
        semantic_contract="descriptive",
        sources=[
            "Schwarcz, Steven L. Systemic Risk (2008)",
            "Kirilenko, A., et al. The Flash Crash: The Impact of High Frequency Trading (2017)",
        ],
        analogs=["market-microstructure", "aml-risk-scoring", "algorithmic-trading"],
        eli5=(
            "If everyone follows the same GPS route, one closed road makes every car "
            "swing into the same side street at the same moment — a traffic jam that "
            "didn't exist until everyone copied each other."
        ),
        analogy=(
            "A crowd at a theatre: one person shouts 'fire', everyone runs for the "
            "same exit, and the crowd itself becomes the danger. The stampede is the "
            "cascade; the rumour was the trigger."
        ),
        example=(
            "The 2010 Flash Crash: a large sell order cascaded through correlated "
            "high-frequency strategies, wiping ~$1 trillion of market value in minutes "
            "before prices recovered — a collapse too fast for any circuit breaker "
            "built for human trading."
        ),
        gap_questions=[
            "Why are correlated models more dangerous than a single bad model?",
            "How do circuit breakers designed for human markets fail in algorithmic ones?",
            "What would a data-level early-warning system for cascades look like?",
        ],
        teach_back=(
            "Explain how a small trigger becomes a systemic cascade through "
            "correlation and feedback, and why data is both the early-warning sensor "
            "and a potential accelerant."
        ),
    ),
    make_concept(
        cid="contestability",
        label="Contestability",
        description=(
            "The right and practical ability of a person to challenge a decision that "
            "affects them, including decisions made or informed by automated systems. "
            "Loss of contestability arises when opaque models, one-way data flows, and "
            "private adjudication remove any meaningful avenue of appeal."
        ),
        category="regulations",
        aliases=["right to contest", "algorithmic contestability", "due process in code"],
        lineage=["republicanism", "legal_philosophy", "critical_theory"],
        epistemic="regulatory",
        normative="kantian_duty",
        ontology_commitment="realist",
        temporal="event_based",
        uncertainty="ambiguity",
        governance="polycentric",
        semantic_contract="constitutive",
        sources=[
            "Hildebrandt, Mireille. Smart Technologies and the End(s) of Law (2015)",
            "Zuboff, Shoshana. The Age of Surveillance Capitalism (2019)",
        ],
        analogs=["ai-aml-surveillance", "regtech", "aml-case-management"],
        eli5=(
            "If a machine quietly puts you on a list you can't see, with reasons you "
            "can't read, and you have no one to appeal to — that's a contestability "
            "problem. Contestability is the door that stays open for 'but wait, that's "
            "wrong about me'."
        ),
        analogy=(
            "A referee in a sport: play only works if the players believe the ref's "
            "call can be questioned and reviewed. Remove the replay and the appeal, "
            "and players stop trusting the game."
        ),
        example=(
            "An AML model flags a customer's account as high-risk; the customer is "
            "denied service with no explanation and no effective appeal. GDPR's "
            "right to explanation and the AI Act's human-oversight duties are attempts "
            "to restore contestability in exactly this situation."
        ),
        gap_questions=[
            "What makes an automated decision contestable in practice, not just in theory?",
            "Why does a 'right to explanation' alone not guarantee contestability?",
            "Where do data engineering and contestability meet?",
        ],
        teach_back=(
            "Explain the difference between being able to request a decision and being "
            "able to contest it, and what systems must expose to make contestation real."
        ),
    ),
    make_concept(
        cid="digital-neofeudalism",
        label="Digital Neofeudalism",
        description=(
            "A speculative-but-dire structural outcome in which private platforms "
            "become de facto jurisdictions: users cannot meaningfully exit, terms of "
            "service function as constitutional law without separation of powers, and "
            "data plays the role of the land — concentrated in a few hands that "
            "govern access, opportunity, and even identity."
        ),
        category="regulations",
        aliases=["platform feudalism", "data feudalism", "technofeudalism"],
        lineage=["critical_theory", "political_philosophy"],
        epistemic="constitutive",
        normative="rawlsian",
        ontology_commitment="constructivist",
        temporal="processual",
        uncertainty="ignorance",
        governance="hierarchical",
        semantic_contract="constitutive",
        sources=[
            "Zuboff, Shoshana. The Age of Surveillance Capitalism (2019)",
            "Lessig, Lawrence. Code and Other Laws of Cyberspace (1999)",
        ],
        analogs=["data-governance", "global-sanctions", "aml-regulatory-framework"],
        eli5=(
            "In a medieval village, the lord owned the land and everyone else paid to "
            "live on it. Digital neofeudalism is when a handful of companies own the "
            "digital 'land' — accounts, attention, data — and everyone else rents."
        ),
        analogy=(
            "A town where one company owns the roads, the market, the courts, and the "
            "records office. You can 'choose' to live there — but leaving means "
            "leaving everything behind."
        ),
        example=(
            "A platform that owns the identity graph, the payment rails, and the "
            "moderation rules: its terms of service can ban a user with no appeal, "
            "while the user's entire economic and social life is entangled in the "
            "platform — exit is nominal, not real."
        ),
        gap_questions=[
            "What makes exit from a platform 'nominal' rather than real?",
            "How does data concentration resemble land concentration?",
            "Which of the triangle's layers most needs constitutional guardrails?",
        ],
        teach_back=(
            "Explain the analogy between feudal land and concentrated data, and why "
            "terms of service are not a substitute for a constitution."
        ),
    ),
]


RELATIONS = [
    ("computational-constitutionalism", "regtech", "influences", 0.8),
    ("compliance-by-design", "data-governance", "requires", 0.9),
    ("compliance-by-design", "aml-regulatory-framework", "implements", 0.8),
    ("compliance-by-design", "computational-constitutionalism", "part_of", 0.7),
    ("regulatory-lag", "aml-regulatory-framework", "influences", 0.7),
    ("algorithmic-cascade", "aml-risk-scoring", "related_to", 0.7),
    ("algorithmic-cascade", "algorithmic-trading", "influences", 0.8),
    ("contestability", "ai-aml-surveillance", "regulates", 0.7),
    ("contestability", "regtech", "influences", 0.7),
    ("digital-neofeudalism", "data-governance", "influences", 0.6),
    ("digital-neofeudalism", "contestability", "related_to", 0.8),
    ("law-markets-data-triangle", "data-governance", "requires", 0.8),
    ("law-markets-data-triangle", "aml-regulatory-framework", "influences", 0.8),
    ("law-markets-data-triangle", "market-microstructure", "influences", 0.8),
    ("compliance-by-design", "aml-continuous-monitoring", "enables", 0.7),
]


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    mgr = OntologyManager.load(ONTOLOGY_PATH)

    added_c = 0
    merged_c = 0
    for concept in CONCEPTS:
        if mgr.get_concept(concept.id) is None:
            mgr.add_concept(concept)
            added_c += 1
            print(f"  [ADD]  concept {concept.id}")
        else:
            mgr.add_concept(concept)  # merge aliases
            merged_c += 1
            if dry_run:
                print(f"  [SKIP] concept {concept.id} — already exists (aliases would merge)")
            else:
                print(f"  [MERG] concept {concept.id} — aliases merged")

    added_r = 0
    for source, target, rtype, strength in RELATIONS:
        if mgr.get_concept(source) is None or mgr.get_concept(target) is None:
            print(f"  [SKIP] relation {source} -{rtype}-> {target} (missing concept)")
            continue
        mgr.add_relation(
            Relation(source_id=source, target_id=target, relation_type=rtype, strength=strength, pillar="cross-pillar")
        )
        added_r += 1
        if dry_run:
            print(f"  [SKIP] relation {source} -{rtype}-> {target} (would add)")
        else:
            print(f"  [ADD]  relation {source} -{rtype}-> {target}")

    if dry_run:
        print(f"\nDry run: {added_c} concepts, {merged_c} existing, {added_r} relations")
        return

    mgr.save(ONTOLOGY_PATH)
    total = sum(len(v) for v in mgr.concepts_by_pillar().values())
    print(f"\nSaved {ONTOLOGY_PATH}")
    print(f"Ontology now has {total} concepts")
    print(f"Added {added_c} concepts, merged {merged_c}, added {added_r} relations")


if __name__ == "__main__":
    main()
