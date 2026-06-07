"""Add 4 new learn lessons covering 2026 knowledge state and behavioral psychology."""
import json
from datetime import datetime, timezone

REGISTRY_PATH = "registry.json"
with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    registry = json.load(f)

existing_slugs = {c["slug"] for c in registry["content"]}

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
DATE = "2026-06-07"

def q(question, options, answer, bloom_level="understand"):
    return {
        "bloom_level": bloom_level, "type": "mc",
        "question": question, "options": options, "answer": answer,
    }

def make_entry(slug, title, description, body_html, tags, pillar, difficulty,
               flashcards, bloom_questions):
    return {
        "slug": slug,
        "language": "en",
        "title": title,
        "description": description,
        "body_html": body_html,
        "category": "lesson",
        "content_type": "learn",
        "tags": tags,
        "created_at": NOW,
        "updated_at": None,
        "pillar": pillar,
        "date_str": DATE,
        "thumbnail_svg": "",
        "og_svg": "",
        "featured_image": "",
        "trending_html": "",
        "analysis_html": "",
        "cross_pillar_html": "",
        "bloom_questions": bloom_questions,
        "flashcards": flashcards,
        "signals": {},
        "source_breakdown": {},
        "quality_metrics": {},
        "lineage": {},
        "quality_flags": [],
        "difficulty": difficulty,
    }

# ─── 1. Crypto AML & Digital Assets ────────────────────────────────────────
crypto_aml = make_entry(
    slug="learn/crypto-aml",
    title="Crypto AML & Digital Assets — Compliance in the Age of DeFi",
    description="Understand how anti-money laundering regulations apply to cryptocurrencies, stablecoins, DeFi protocols, and digital asset ecosystems — including blockchain analytics, the Travel Rule, and 2026 regulatory developments.",
    body_html="""<p>By 2026, stablecoin transaction volumes have reached $9.8 trillion annually, and 61% of financial institutions now prioritize real-time AML/CFT monitoring for crypto-asset transactions. The era of crypto operating outside regulatory frameworks is over — compliance is now a first-class requirement for any digital asset business.</p>

<h2>Why Crypto AML Matters</h2>
<p>Cryptocurrencies present unique AML challenges: pseudonymous transactions, instant cross-border movement, decentralized finance (DeFi) protocols with no central intermediary, and privacy-enhancing technologies like mixers and zero-knowledge proofs. Criminal organizations exploit these features for ransomware payments, darknet market transactions, and laundering proceeds through decentralized exchanges.</p>
<p>The <strong>Financial Action Task Force (FATF)</strong> has updated its Recommendations to cover virtual asset service providers (VASPs), requiring them to implement the same AML/CFT measures as traditional financial institutions. By 2026, 128 jurisdictions have introduced or are introducing crypto-specific regulations.</p>

<h2>The Travel Rule for Crypto</h2>
<p>FATF Recommendation 16 (the "Travel Rule") requires VASPs to share originator and beneficiary information for transactions above a threshold (typically $1,000). This applies to all virtual asset transfers. Implementation uses specialized travel rule protocols like <strong>OpenVASP</strong>, <strong>TRISA</strong>, and the <strong>IVMS 101</strong> data standard. As of 2026, the Travel Rule is enforced in the EU (MiCA), US (FinCEN guidance), Singapore, Japan, and UAE.</p>

<h2>Blockchain Analytics & Forensics</h2>
<p>Blockchain analytics tools — Chainalysis, TRM Labs, Elliptic — trace transaction flows across public ledgers. Key techniques include:</p>
<ul>
<li><strong>Cluster analysis:</strong> Grouping addresses controlled by the same entity using heuristic rules (common input, change address detection).</li>
<li><strong>Attribution tagging:</strong> Labeling addresses associated with known services, exchanges, mixers, or criminal entities.</li>
<li><strong>Risk scoring:</strong> Assigning risk scores to addresses based on their transaction history and proximity to known illicit activity.</li>
<li><strong>Graph analysis:</strong> Visualizing complex transaction networks to uncover layering patterns and fund movement across hundreds of hops.</li>
</ul>

<h2>DeFi Compliance</h2>
<p>Decentralized finance poses the hardest challenge: no central operator, no KYC, instant composability. The 2026 regulatory approach focuses on:</p>
<ul>
<li><strong>Front-end accountability:</strong> Requiring DeFi interfaces and dApp front-ends to implement geoblocking and access controls.</li>
<li><strong>Wallet-level screening:</strong> Mandating that wallet providers screen addresses before processing transactions.</li>
<li><strong>Stablecoin regulation:</strong> The EU's MiCA framework and US stablecoin bills require issuers to hold reserves, register as e-money institutions, and comply with AML obligations.</li>
<li><strong>On-chain analytics obligations:</strong> Some jurisdictions now require DeFi protocols to integrate real-time screening at the smart contract level.</li>
</ul>

<h2>2026 Landscape</h2>
<p>The convergence of AI and blockchain analytics is accelerating. Machine learning models now detect suspicious patterns in real-time across multiple blockchains simultaneously. The AI-native AML platforms emerging in 2026 combine transaction monitoring, sanctions screening, and fraud detection into unified systems — the same convergence happening in traditional finance.</p>
<p>For a refresher on AML fundamentals, revisit <a href="/learn/aml-basics/">AML Fundamentals</a>. To understand the data infrastructure needed for real-time screening, see <a href="/learn/dataops-introduction/">Introduction to DataOps</a>.</p>""",
    tags=["aml", "crypto", "defi", "stablecoins", "blockchain", "compliance", "travel-rule", "fintech"],
    pillar="aml",
    difficulty="intermediate",
    flashcards=[
        {"term": "Travel Rule", "definition": "FATF Recommendation 16 requiring VASPs to share originator and beneficiary information for virtual asset transactions above a threshold."},
        {"term": "DeFi", "definition": "Decentralized Finance — blockchain-based financial services operating without traditional intermediaries, using smart contracts for automated execution."},
        {"term": "Blockchain Analytics", "definition": "Techniques for tracing and attributing cryptocurrency transactions on public ledgers using cluster analysis, graph analysis, and risk scoring."},
        {"term": "MiCA", "definition": "Markets in Crypto-Assets Regulation — the EU's comprehensive regulatory framework for digital assets, stablecoins, and crypto service providers."},
        {"term": "VASP", "definition": "Virtual Asset Service Provider — any entity that exchanges, transfers, or safekeeps virtual assets on behalf of customers, subject to AML obligations."},
    ],
    bloom_questions=[
        q("Which FATF Recommendation requires VASPs to share customer information for crypto transactions?",
          ["Recommendation 10 (Record Keeping)", "Recommendation 16 (Travel Rule)", "Recommendation 22 (DNFBPs)", "Recommendation 29 (Financial Intelligence Units)"], 1, "remember"),
        q("A crypto exchange detects a wallet cluster with high-risk scores based on proximity to known ransomware addresses. This is an example of:",
          ["Travel Rule compliance", "On-chain analytics and risk scoring", "KYC verification", "Smart contract auditing"], 1, "understand"),
        q("A DeFi protocol has no central operator and no KYC process. Under 2026 regulations, which compliance approach is most applicable?",
          ["No regulation applies to DeFi", "Front-end geoblocking and wallet-level screening", "The protocol must shut down", "Only stablecoin transactions are regulated"], 1, "apply"),
        q("Why does the pseudonymous nature of cryptocurrency create a gap in traditional AML frameworks?",
          ["Cryptocurrency is not real money", "Transactions occur without a trusted intermediary who can identify the parties", "Blockchain transactions cannot be monitored", "All crypto is already compliant"], 1, "analyze"),
        q("An institution processes $50M in stablecoin transactions monthly. What is the most critical compliance investment for 2026?",
          ["A new marketing website", "Real-time blockchain transaction monitoring and Travel Rule solution", "More customer service staff", "Office expansion"], 1, "evaluate"),
    ],
)

# ─── 2. Semiconductor Supply Chain ─────────────────────────────────────────
semicon = make_entry(
    slug="learn/semiconductor-supply-chain",
    title="Semiconductor Supply Chain — Geopolitics, Markets, and the $1T Chip Industry",
    description="Explore the global semiconductor supply chain in 2026: $975 billion market, AI-driven demand reshaping fab capacity, geopolitical tensions, material scarcity, and strategic sourcing strategies.",
    body_html="""<p>The semiconductor industry is projected to reach $975 billion in global sales in 2026 — a 26% year-over-year increase driven overwhelmingly by AI. Yet the same chips powering the AI revolution represent under 0.2% of total unit volume. This asymmetry creates structural tensions across the entire supply chain, from raw material extraction to fab capacity allocation.</p>

<h2>Market Structure in 2026</h2>
<p>AI logic and memory chips account for roughly $500 billion — over half of industry revenue — but fewer than 20 million of the 1.05 trillion chips sold annually. The remaining 99.8% of chips (automotive microcontrollers, industrial sensors, power management ICs) compete for older-node fab capacity that is increasingly squeezed as foundries pivot to high-margin advanced nodes.</p>

<h2>The AI vs. Auto Conflict</h2>
<p>Data centers are projected to consume 70% of all memory chips produced in 2026. This structural reallocation creates a new scarcity crisis for the automotive industry, which relies on older "foundational" nodes (28nm-180nm) for 95% of vehicle chips. Analysts forecast up to 600,000 fewer vehicles may be built in 2026 due to chip shortages. Unlike the pandemic-era demand shock (2021-2024), this is a permanent reallocation driven by AI's superior margins.</p>

<h2>Geopolitical & Material Risks</h2>
<p>Three critical risks shape the 2026 landscape:</p>
<ul>
<li><strong>Export controls:</strong> US restrictions on advanced chip exports to China have reshaped global supply chains, driving China's push for self-sufficiency and creating parallel supply chains.</li>
<li><strong>Helium crisis:</strong> EUV lithography requires massive helium volumes — 2x per wafer at 2nm vs 7nm. Helium is non-renewable, and prices have stabilized at 3x pre-AI levels. A single pressure interruption can ruin a batch of wafers worth tens of millions of dollars.</li>
<li><strong>Tungsten supply:</strong> Tungsten prices are surging due to geopolitical decoupling, squeezing 2nm node margins. China controls 80% of global tungsten refining capacity.</li>
</ul>

<h2>Advanced Packaging Over Node Scaling</h2>
<p>With Moore's Law slowing, performance gains increasingly come from advanced packaging (2.5D/3D), heterogeneous integration, and chiplet architectures rather than pure process node shrinks. Thermal management, interconnect density, and package-level yield are now strategic differentiators. TSMC's CoWoS (Chip-on-Wafer-on-Substrate) packaging capacity is oversubscribed through 2027.</p>

<h2>Strategic Sourcing</h2>
<p>Companies are moving from just-in-time to just-in-case inventory strategies. Key practices include: multi-sourcing from geographically dispersed fabs, maintaining 12+ months of buffer inventory for critical nodes, real-time market intelligence on lead times and allocation, and investing in materials supply contracts for helium and specialty gases.</p>

<p>For an introduction to market signals and analysis frameworks, see <a href="/learn/market-analysis/">How to Analyse Market Signals</a>. The data pipelines that monitor these supply chains are explored in <a href="/learn/open-source-data-stack/">Building an Open Source Data Stack</a>.</p>""",
    tags=["semiconductors", "supply-chain", "markets", "stock", "manufacturing", "geopolitics", "ai-hardware", "trade"],
    pillar="stock",
    difficulty="intermediate",
    flashcards=[
        {"term": "Foundational Nodes", "definition": "Mature semiconductor process nodes (28nm-180nm) used for automotive, industrial, and IoT chips — facing capacity squeeze as fabs prioritize advanced nodes."},
        {"term": "EUV Lithography", "definition": "Extreme Ultraviolet Lithography — advanced chip manufacturing technique using 13.5nm wavelength light, requiring massive helium volumes for cooling."},
        {"term": "CoWoS", "definition": "Chip-on-Wafer-on-Substrate — TSMC's advanced 2.5D packaging technology that stacks chips side-by-side on a silicon interposer for higher performance density."},
        {"term": "Heterogeneous Integration", "definition": "Packaging technique combining chips of different sizes, nodes, and functions in a single package — the primary performance scaling approach as Moore's Law slows."},
        {"term": "Just-in-Case Inventory", "definition": "Supply chain strategy maintaining strategic buffer stock of critical components to hedge against disruption, replacing just-in-time in constrained markets."},
    ],
    bloom_questions=[
        q("What percentage of total semiconductor unit volume do AI chips represent despite generating over half of industry revenue?",
          ["Less than 0.2%", "About 5%", "Approximately 25%", "More than 50%"], 0, "remember"),
        q("A tier-1 automotive supplier cannot secure enough 28nm microcontrollers for its ECUs. What is the most likely cause in 2026?",
          ["COVID-era supply chain disruptions continue", "Foundries have reallocated capacity to high-margin AI chips", "Automakers reduced their orders", "28nm fabs no longer exist"], 1, "understand"),
        q("A fab experiences a 4-hour helium pressure drop during EUV lithography. What is the likely consequence?",
          ["Slight reduction in throughput", "Potential loss of an entire wafer batch worth millions", "No impact — helium is non-critical", "Production continues with air cooling"], 1, "apply"),
        q("Why is advanced packaging becoming more important than node shrinks for semiconductor performance?",
          ["Packaging is cheaper than node shrinks", "Moore's Law is slowing, so performance gains come from integration and interconnect density", "Customers prefer packaged chips", "Node shrinks are illegal in some jurisdictions"], 1, "analyze"),
        q("A procurement manager must choose between a single-source advanced-node supplier and a multi-source foundational-node strategy. Which factor most justifies the multi-source approach?",
          ["Advanced nodes are obsolete", "Concentration risk from geopolitical tensions and material scarcity makes single-sourcing dangerous for critical components", "Multi-source is always cheaper", "Foundational nodes have higher margins"], 1, "evaluate"),
    ],
)

# ─── 3. Gene Editing & CRISPR ──────────────────────────────────────────────
crispr = make_entry(
    slug="learn/crispr-gene-editing",
    title="Gene Editing & CRISPR — From Lab Bench to Approved Medicine",
    description="Trace the journey of CRISPR gene editing from a bacterial defense system to FDA-approved therapies, exploring the science, 2026 clinical trial landscape, ethical frameworks, and what comes next.",
    body_html="""<p>In December 2023, the FDA approved Casgevy (exagamglogene autotemcel) — the first therapy built on CRISPR-Cas9 gene editing — for sickle cell disease. By 2026, approximately 250 clinical trials involving gene-editing therapeutics are active worldwide, spanning oncology, cardiovascular disease, autoimmune conditions, and rare genetic disorders. Gene editing has moved from laboratory breakthrough to approved medicine.</p>

<h2>How CRISPR-Cas9 Works</h2>
<p>CRISPR-Cas9 is a bacterial immune system repurposed for precise DNA editing. The system has two components: a <strong>guide RNA (gRNA)</strong> that matches a target DNA sequence, and the <strong>Cas9 enzyme</strong> that cuts both strands of DNA at that location. The cell's natural repair mechanisms then kick in:</p>
<ul>
<li><strong>Non-homologous end joining (NHEJ):</strong> The cell stitches the break back together, often disrupting the target gene by introducing small insertions or deletions (indels). Useful for <em>knocking out</em> genes.</li>
<li><strong>Homology-directed repair (HDR):</strong> If a repair template is provided, the cell uses it to precisely replace the DNA sequence. Useful for <em>correcting</em> mutations.</li>
</ul>

<h2>Next-Generation Editing</h2>
<p>CRISPR-Cas9 was just the beginning. By 2026, several refinements have matured:</p>
<ul>
<li><strong>Base editing:</strong> Converts one DNA base pair into another without making a double-strand break. For example, C•G to T•A. Useful for correcting point mutations that cause ~60% of human genetic diseases.</li>
<li><strong>Prime editing:</strong> A "search-and-replace" approach that directly writes new genetic information into a target site. Offers greater precision and fewer off-target effects than Cas9.</li>
<li><strong>Epigenetic editing:</strong> Modifies gene <em>expression</em> without changing the underlying DNA sequence — turning genes on or off reversibly.</li>
</ul>

<h2>Clinical Landscape 2026</h2>
<p>The ~250 active clinical trials break down approximately as: 80 in oncology/CAR-T therapies, 50 in blood disorders, 30 in cardiovascular disease, 25 in autoimmune conditions, 25 in rare genetic diseases, 20 in infectious disease. Casgevy's success in sickle cell disease — 29 of 31 patients achieving complete freedom from vaso-occlusive crises — proved the model. The next frontier is <em>in vivo</em> delivery: editing cells inside the body rather than extracting, editing, and reinfusing them.</p>

<h2>Ethical & Regulatory Frameworks</h2>
<p>Key governance questions include: <strong>germline editing</strong> (heritable changes to embryos — banned or strictly controlled in most countries), <strong>equity of access</strong> (Casgevy's list price is $2.2M per patient), <strong>off-target effects</strong> (unintended edits that could cause cancer), and <strong>informed consent</strong> for permanent genetic modifications. The FDA and EMA have established dedicated gene therapy frameworks, and the International Commission on the Clinical Use of Human Germline Genome Editing provides global guidance.</p>

<p>For the methodological foundations of evaluating scientific claims like those in CRISPR research, see <a href="/learn/science-method/">Scientific Reasoning in Research Synthesis</a>. To understand the data pipelines powering genomics research, explore <a href="/learn/data-quality-engineering/">Data Quality Engineering</a>.</p>""",
    tags=["science", "crispr", "gene-editing", "biotech", "genomics", "medicine", "bioethics", "fda"],
    pillar="science",
    difficulty="intermediate",
    flashcards=[
        {"term": "Cas9", "definition": "CRISPR-associated protein 9 — an endonuclease enzyme that cuts DNA at a location specified by a guide RNA, forming the core of the CRISPR gene-editing system."},
        {"term": "Base Editing", "definition": "A precision gene-editing technique that converts one DNA base pair to another without creating a double-strand break — useful for correcting point mutations."},
        {"term": "Casgevy", "definition": "The first FDA-approved CRISPR-based therapy (Dec 2023), treating sickle cell disease by editing patients' own stem cells to produce healthy hemoglobin."},
        {"term": "NHEJ vs HDR", "definition": "Non-homologous end joining (disrupts genes by introducing indels) vs homology-directed repair (precise replacement using a template) — the two DNA repair pathways after Cas9 cutting."},
        {"term": "In Vivo Delivery", "definition": "Editing genes inside the living body using viral vectors or lipid nanoparticles — the next frontier, eliminating the need to extract, edit, and reinfuse cells."},
    ],
    bloom_questions=[
        q("What is the role of the guide RNA (gRNA) in CRISPR-Cas9?",
          ["It cuts the DNA", "It matches and binds to the target DNA sequence", "It repairs the DNA break", "It delivers the Cas9 protein to the nucleus"], 1, "remember"),
        q("A scientist wants to correct a single point mutation in a patient's DNA without creating a double-strand break. Which technique should they use?",
          ["CRISPR-Cas9 with NHEJ", "Base editing", "Standard gene therapy using a viral vector", "RNA interference"], 1, "apply"),
        q("Why might Casgevy's $2.2M price tag create ethical concerns beyond typical drug pricing debates?",
          ["The drug does not work", "It represents a permanent genetic modification, raising questions about long-term value and equity of access", "Insurance never covers gene therapies", "The price is lower than comparable drugs"], 1, "evaluate"),
        q("Most current CRISPR clinical trials require extracting cells, editing them in a lab, and reinfusing them. What is the key advantage of in vivo delivery?",
          ["Lower cost", "Ability to edit cells that cannot be extracted (e.g., brain, heart)", "Higher precision", "FDA approval is faster"], 1, "analyze"),
        q("How does prime editing differ from base editing?",
          ["Prime editing is slower", "Prime editing writes new genetic information via a search-and-replace mechanism, while base editing only converts one base pair to another", "Base editing works only in bacteria", "Prime editing does not use Cas proteins"], 1, "understand"),
    ],
)

# ─── 4. Behavioral Design & Learning Psychology ────────────────────────────
behavioral = make_entry(
    slug="learn/behavioral-design-learning",
    title="Behavioral Design for Learning — Psychology Behind Effective Education Platforms",
    description="Explore the behavioral psychology principles that make learning platforms like Duolingo, Khan Academy, and Brilliant effective — and how you can apply Fogg's Behavior Model, habit loops, and gamification to your own learning practice.",
    body_html="""<p>Why do millions of people voluntarily practice French at 7 AM on Duolingo? Why do Brilliant users spend hours solving math problems for fun? The answer is not the content — it is the behavioral design surrounding the content. The most effective learning platforms are not just educational tools; they are habit-forming systems built on well-understood psychological principles.</p>

<h2>Fogg's Behavior Model</h2>
<p>Stanford psychologist BJ Fogg's Behavior Model states that for a behavior to occur, three elements must converge: <strong>Motivation</strong>, <strong>Ability</strong>, and a <strong>Prompt</strong> (also called a trigger). Learning platforms apply this systematically:</p>
<ul>
<li><strong>Motivation:</strong> Show real-world relevance, connect to learner goals, use progress streaks to create commitment. Duolingo's streak count leverages loss aversion — you do not want to break the chain.</li>
<li><strong>Ability:</strong> Make the first lesson absurdly easy (2 minutes, one question). Reduce friction — no login wall, instant start. Khan Academy's mastery-based progression lets learners move at their own pace, removing the anxiety of keeping up.</li>
<li><strong>Prompt:</strong> Push notifications, email reminders, the "Continue Learning" section on this very homepage. The most effective prompts are <em>contextual</em> — appearing when motivation and ability are already high.</li>
</ul>

<h2>The Hook Model</h2>
<p>Nir Eyal's Hook Model describes a four-step cycle for habit formation: <strong>Trigger → Action → Variable Reward → Investment</strong>. Top learning platforms embed this cycle:</p>
<ul>
<li><strong>Trigger:</strong> External (notification: "Your daily lesson is ready!") or internal (feeling bored, opening the app habitually).</li>
<li><strong>Action:</strong> The simplest possible behavior — answer one question, flip one flashcard. Duolingo's lessons are designed to take fewer than 5 minutes.</li>
<li><strong>Variable Reward:</strong> This is the key. Fixed rewards (always the same prize) stop being interesting. <em>Variable</em> rewards — surprise bonus XP, unlocking a new level, a funny animation — keep the brain engaged because dopamine peaks during <em>anticipation</em>, not receipt. This is why Duolingo's "chest" with random XP amounts is more engaging than a fixed daily bonus.</li>
<li><strong>Investment:</strong> The user puts something into the system — time, effort, or data — that makes the service more valuable and increases the likelihood of returning. Writing flashcards, building a profile, maintaining a streak.</li>
</ul>

<h2>Gamification Mechanics</h2>
<p>Common gamification elements backed by behavioral psychology:</p>
<ul>
<li><strong>Progress bars & mastery tracking:</strong> The <em>goal gradient effect</em> shows that people work harder as they approach a goal. The reading progress bar on every AcaciaFund article uses this principle.</li>
<li><strong>Spaced repetition:</strong> Reviewing material at increasing intervals exploits the <em>spacing effect</em> — one of the most robust findings in cognitive psychology. Flashcards with flip interaction implement this.</li>
<li><strong>Completion bias:</strong> People are disproportionately motivated to finish what they've started. Lesson completion checkmarks and progress counters tap into this.</li>
<li><strong>Social comparison:</strong> Leaderboards create motivation through social proof. (AcaciaFund does not use leaderboards to preserve privacy and reduce anxiety.)</li>
</ul>

<h2>Learning from the Best</h2>
<p>What makes top platforms effective is not any single feature but the <em>integration</em> of these principles into a coherent system. Duolingo combines streak (motivation) + bite-sized lessons (ability) + notifications (prompt) + variable XP (reward). Khan Academy combines mastery-based progression (ability) + energy points (reward) + skill trees (investment). Each platform aligns all elements of Fogg's model toward the single goal of daily practice.</p>

<h2>Applying This to Your Learning</h2>
<ul>
<li><strong>Lower the barrier:</strong> Commit to just 2 minutes per day. The hardest part is starting.</li>
<li><strong>Use implementation intentions:</strong> "I will study at [time] in [location] for [duration]." This turns a vague goal into a concrete trigger.</li>
<li><strong>Track your streak:</strong> Consistency matters more than duration. Mark a lesson complete every day, even if you only review one flashcard.</li>
<li><strong>Embrace variable rewards:</strong> Alternate between different subjects and lesson types. The novelty itself reinforces the habit.</li>
</ul>

<p>This lesson itself is an example of behavioral design: it uses cross-references (social proof), a reading progress bar (goal gradient), and flashcards (spaced repetition). To explore the scientific reasoning behind evaluating claims about learning techniques, see <a href="/learn/science-method/">Scientific Reasoning in Research Synthesis</a>.</p>""",
    tags=["psychology", "behavioral-design", "learning", "gamification", "habits", "education", "ux", "meta"],
    pillar="science",
    difficulty="intermediate",
    flashcards=[
        {"term": "Fogg's Behavior Model", "definition": "B=MAP — Behavior occurs when Motivation, Ability, and a Prompt converge simultaneously. All three must be present for a behavior to happen."},
        {"term": "Hook Model", "definition": "Nir Eyal's four-step habit loop: Trigger → Action → Variable Reward → Investment. Creates repeated engagement cycles that form habits."},
        {"term": "Variable Reward", "definition": "A reward that varies unpredictably in size or type — more engaging than fixed rewards because dopamine peaks during anticipation, not receipt."},
        {"term": "Goal Gradient Effect", "definition": "The psychological phenomenon where people work harder and faster as they approach a goal — exploited by progress bars and completion trackers."},
        {"term": "Spacing Effect", "definition": "The robust finding that information is better retained when reviewed at increasing intervals over time, rather than massed in a single session."},
    ],
    bloom_questions=[
        q("According to Fogg's Behavior Model, which three elements must converge for a behavior to occur?",
          ["Habit, Reward, and Consistency", "Motivation, Ability, and Prompt", "Trigger, Action, and Investment", "Knowledge, Practice, and Feedback"], 1, "remember"),
        q("Why are variable rewards more engaging than fixed rewards?",
          ["They are bigger", "Dopamine peaks during anticipation of unpredictable outcomes", "Fixed rewards are always boring", "Variable rewards are easier to implement"], 1, "understand"),
        q("A learning app sends a push notification at 8 AM, the user opens it and answers one question, receives a random XP bonus, and the app tracks their streak. Which Hook Model stages are being activated?",
          ["Investment → Trigger → Action", "Trigger → Action → Variable Reward → Investment", "Motivation → Ability → Prompt", "Reward → Habit → Trigger"], 1, "apply"),
        q("Why does the goal gradient effect make a progress bar showing 85% more motivating than one showing 15%, even if the absolute remaining work is the same?",
          ["85% is closer to completion", "The perceived effort-to-reward ratio shifts — each unit of work feels more impactful near the goal", "Progress bars only work above 50%", "People cannot read progress under 50%"], 1, "analyze"),
        q("A platform adds badges, leaderboards, and streak counters but sees only short-term engagement gains. What is the most likely explanation?",
          ["Users do not like gamification", "The system relies only on extrinsic motivation without building intrinsic interest in the content", "Badges are ineffective", "The platform needs more game mechanics"], 1, "evaluate"),
    ],
)

# ─── Add to registry ────────────────────────────────────────────────────────
new_lessons = [crypto_aml, semicon, crispr, behavioral]
for lesson in new_lessons:
    if lesson["slug"] not in existing_slugs:
        registry["content"].append(lesson)
        print(f"  Added: {lesson['slug']}")
    else:
        print(f"  Skipped (exists): {lesson['slug']}")

with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

print()

# Summary
for c in registry["content"]:
    if c.get("content_type") == "learn":
        bq = len(c.get("bloom_questions", []))
        fc = len(c.get("flashcards", []))
        body = len(c.get("body_html", "") or "")
        print(f"  {c['slug']:40s} body={body:>5}  fc={fc}  bq={bq}  diff={c.get('difficulty','?')}")
