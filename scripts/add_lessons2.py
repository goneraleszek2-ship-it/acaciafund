"""Add 4 new learn lessons — TBML/sanctions, behavioral finance, meta-analysis, data ethics."""
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
        "slug": slug, "language": "en", "title": title, "description": description,
        "body_html": body_html, "category": "lesson", "content_type": "learn",
        "tags": tags, "created_at": NOW, "updated_at": None, "pillar": pillar,
        "date_str": DATE, "thumbnail_svg": "", "og_svg": "", "featured_image": "",
        "trending_html": "", "analysis_html": "", "cross_pillar_html": "",
        "bloom_questions": bloom_questions, "flashcards": flashcards,
        "signals": {}, "source_breakdown": {}, "quality_metrics": {},
        "lineage": {}, "quality_flags": [], "difficulty": difficulty,
    }

# ─── 1. Trade-Based ML & Sanctions Screening ───────────────────────────────
tbml = make_entry(
    slug="learn/trade-based-ml-sanctions",
    title="Trade-Based Money Laundering & Sanctions — The $2 Trillion Blind Spot",
    description="Explore trade-based money laundering techniques, sanctions screening frameworks, beneficial ownership transparency, and the 2026 regulatory landscape of geopolitical fragmentation.",
    body_html="""<p>Trade-based money laundering (TBML) is one of the oldest and most difficult-to-detect methods of moving illicit value across borders. By 2026, 38% of financial crime compliance officers identify TBML as a top-three risk, and sanctions regimes have become more fragmented than at any point in the last decade. Understanding both is essential for any AML professional.</p>

<h2>Trade-Based Money Laundering</h2>
<p>TBML exploits the complexity of international trade to obscure the movement of value. Unlike wire transfers — which leave electronic trails — trade transactions involve paper documentation, multiple intermediaries, and physical goods, creating abundant opportunities for concealment.</p>

<h3>Common TBML Techniques</h3>
<ul>
<li><strong>Over-invoicing / Under-invoicing:</strong> Misrepresenting the price of goods to move value. Over-invoicing pays excess funds to a foreign supplier (value leaves the country); under-invoicing allows the importer to resell goods at a profit offshore (value stays abroad).</li>
<li><strong>Multiple invoicing:</strong> Submitting the same invoice to multiple banks for financing, collecting funds from each before anyone detects the duplication.</li>
<li><strong>Over- / under-shipment:</strong> Shipping more or fewer goods than the invoice states, with the discrepancy being the laundered amount.</li>
<li><strong>Phantom shipments:</strong> Creating invoices and customs documents for goods that do not exist. The funds pay for nothing, and the documentation is fabricated.</li>
<li><strong>Misdescription of goods:</strong> Shipping high-value, hard-to-price items (art, antiques, scrap metal) at manipulated valuations that are difficult for customs to verify.</li>
</ul>

<h2>Sanctions Screening in 2026</h2>
<p>The sanctions landscape has fragmented significantly. The US (OFAC), EU, UK, and UN maintain distinct sanctions lists that increasingly diverge. Key 2026 developments:</p>
<ul>
<li><strong>Secondary sanctions:</strong> The US has expanded secondary sanctions targeting entities that do business with sanctioned jurisdictions, creating extraterritorial compliance obligations.</li>
<li><strong>Crypto sanctions:</strong> OFAC now sanctions specific blockchain addresses and requires VASPs to screen all on-chain transactions — not just fiat on/off ramps.</li>
<li><strong>False positive inflation:</strong> Sanctions list volumes have grown 300% since 2020, with expanding criteria that capture more benign entities. Efficient screening requires fuzzy matching, aliases, and risk-based threshold tuning.</li>
<li><strong>Real-time screening:</strong> Payment messages (ISO 20022) now carry structured beneficiary ownership data, enabling automated screening at the transaction level rather than batch processing.</li>
</ul>

<h2>Beneficial Ownership</h2>
<p>The 2026 push for beneficial ownership transparency is the most significant structural change in AML. The US Corporate Transparency Act (effective 2024-2026) requires all US companies to report their beneficial owners to FinCEN's beneficial ownership registry. The EU's 6th AML Directive mandates centralized beneficial ownership registers accessible to obliged entities. The challenge: 99% of US firms acknowledge limitations in their ability to verify beneficial ownership data, and registers across jurisdictions are not yet interoperable.</p>

<p>For the fundamentals of AML compliance, revisit <a href="/learn/aml-basics/">AML Fundamentals</a>. To understand the blockchain analytics side of sanctions screening, see <a href="/learn/crypto-aml/">Crypto AML & Digital Assets</a>.</p>""",
    tags=["aml", "tbml", "sanctions", "trade-finance", "ofac", "beneficial-ownership", "compliance", "financial-crime"],
    pillar="aml",
    difficulty="intermediate",
    flashcards=[
        {"term": "TBML", "definition": "Trade-Based Money Laundering — the process of disguising illicit funds through trade transactions by misrepresenting price, quantity, or quality of goods."},
        {"term": "Over-Invoicing", "definition": "A TBML technique where goods are invoiced above market value, allowing excess funds to be transferred to a foreign supplier as legitimate trade payments."},
        {"term": "OFAC", "definition": "Office of Foreign Assets Control — the US Treasury agency that administers and enforces economic and trade sanctions against targeted jurisdictions and entities."},
        {"term": "Beneficial Ownership Register", "definition": "A centralized database requiring companies to disclose the natural persons who ultimately own or control them — key to preventing anonymous shell company abuse."},
        {"term": "Secondary Sanctions", "definition": "Sanctions targeting non-US entities that do business with sanctioned jurisdictions, creating extraterritorial compliance obligations for global financial institutions."},
    ],
    bloom_questions=[
        q("A company invoices $2M for electronic components that have a market value of $500K. Which TBML technique does this describe?",
          ["Phantom shipping", "Over-invoicing", "Multiple invoicing", "Misdescription of goods"], 1, "remember"),
        q("Why is TBML particularly difficult to detect compared to wire transfer-based money laundering?",
          ["TBML amounts are always small", "Trade transactions involve paper documents, physical goods, and multiple intermediaries — creating many opportunities to obscure value", "TBML is legal in most jurisdictions", "Banks do not monitor trade transactions"], 1, "understand"),
        q("A compliance team receives 10,000 sanctions alert hits per day with a 99% false positive rate. What is the most effective response?",
          ["Hire more analysts", "Tune screening thresholds using risk-based calibration and fuzzy matching logic", "Ignore alerts under $10,000", "Block all transactions from flagged countries"], 1, "apply"),
        q("How does the fragmentation of US, EU, and UK sanctions lists create compliance risk for a global bank?",
          ["Sanctions are voluntary", "A transaction cleared by one jurisdiction's list may violate another's, creating conflicting obligations", "Fragmentation reduces compliance costs", "Lists are identical in practice"], 1, "analyze"),
        q("A beneficial ownership registry reveals that a shell company's nominal director is a local lawyer, but the actual controlling party is a politically exposed person from a high-risk jurisdiction. What should the filing institution do?",
          ["Accept the filing as-is — the lawyer is the legal owner", "Apply enhanced due diligence and escalate for potential SAR filing based on the undisclosed beneficial owner", "Close the account immediately", "Report to customs authorities"], 1, "evaluate"),
    ],
)

# ─── 2. Behavioral Finance & Portfolio Theory ──────────────────────────────
behav_fin = make_entry(
    slug="learn/behavioral-finance-portfolio",
    title="Behavioral Finance & Portfolio Theory — Mind, Market, and Money",
    description="Understand how cognitive biases distort financial decision-making, how modern portfolio theory provides a rational framework, and how to combine both for better investment outcomes.",
    body_html="""<p>Markets are not perfectly rational. Prices deviate from fundamental value. Investors hold losing stocks too long and sell winners too early. These patterns are not random noise — they are systematic, predictable, and rooted in human psychology. Behavioral finance studies these patterns, while portfolio theory provides the mathematical framework for managing their consequences.</p>

<h2>Prospect Theory & Loss Aversion</h2>
<p>Daniel Kahneman and Amos Tversky's prospect theory (2002 Nobel Prize) showed that losses hurt roughly <em>twice as much</em> as equivalent gains feel good. This asymmetry — <strong>loss aversion</strong> — explains many market anomalies: the equity risk premium (investors demand higher returns to compensate for the pain of potential losses), the disposition effect (selling winners too early and holding losers too long), and the prevalence of portfolio insurance strategies.</p>

<h2>Cognitive Biases in Trading</h2>
<ul>
<li><strong>Overconfidence bias:</strong> 74% of retail investors believe they have above-average stock-picking ability. Overconfidence leads to excessive trading, under-diversification, and lower net returns. Men trade 45% more than women, reducing their net returns by 2.65 percentage points annually (Barber & Odean, 2001).</li>
<li><strong>Confirmation bias:</strong> Seeking information that confirms existing beliefs while ignoring contradictory evidence. In markets, this means holding a position after the thesis breaks because you only read bullish analysis.</li>
<li><strong>Anchoring:</strong> Fixating on a reference price (e.g., what you paid for a stock) rather than current fundamentals. A stock purchased at $100 that now trades at $60 feels like a "loss" even if the company's prospects have permanently deteriorated.</li>
<li><strong>Herding:</strong> Following the crowd — buying what's rising and selling what's falling. Herding amplifies bubbles (meme stocks, crypto manias) and crashes (bank runs, flash crashes).</li>
<li><strong>Recency bias:</strong> Overweighting recent events in forecasting. After a bull market, investors expect continued gains; after a crash, they expect further declines. This drives momentum and mean-reversion patterns.</li>
</ul>

<h2>Modern Portfolio Theory (MPT)</h2>
<p>Harry Markowitz's MPT (1990 Nobel Prize) shows that portfolio risk is not the average of individual asset risks, but depends on <em>correlations</em> between assets. The key insight: diversification across assets with low or negative correlations reduces portfolio volatility without proportionally reducing expected returns. The <strong>efficient frontier</strong> represents the set of portfolios offering the highest expected return for each level of risk.</p>

<h2>The Fed & Macro Context</h2>
<p>Central bank policy is the dominant macro factor for portfolio construction in 2026. The Federal Reserve's interest rate decisions, quantitative tightening/easing, and forward guidance affect all asset classes simultaneously — breaking the low-correlation assumptions that MPT relies on. In 2022, stocks and bonds both fell (correlation turned positive), devastating traditional 60/40 portfolios. Portfolio construction in 2026 requires hedging macro risk through alternative assets (commodities, infrastructure, managed futures) and dynamic asset allocation.</p>

<p>For the foundations of market signal interpretation, see <a href="/learn/market-analysis/">How to Analyse Market Signals</a>. The data infrastructure for portfolio analytics is covered in <a href="/learn/open-source-data-stack/">Building an Open Source Data Stack</a>.</p>""",
    tags=["markets", "stock", "behavioral-finance", "psychology", "portfolio-theory", "trading", "macro", "fed", "risk-management"],
    pillar="stock",
    difficulty="intermediate",
    flashcards=[
        {"term": "Loss Aversion", "definition": "The psychological principle that losses hurt approximately twice as much as equivalent gains feel good — a core finding of Kahneman and Tversky's prospect theory."},
        {"term": "Disposition Effect", "definition": "The tendency to sell winning investments too early (locking in gains) and hold losing investments too long (hoping for recovery), driven by loss aversion."},
        {"term": "Efficient Frontier", "definition": "The set of optimal portfolios offering the highest expected return for each level of risk — the core output of Modern Portfolio Theory."},
        {"term": "Overconfidence Bias", "definition": "The systematic tendency to overestimate one's own abilities — 74% of retail investors believe they have above-average stock-picking skill."},
        {"term": "Correlation Breakdown", "definition": "A period when historically low-correlated asset classes (e.g., stocks and bonds) move together, breaking diversification assumptions of MPT."},
    ],
    bloom_questions=[
        q("According to prospect theory, how much more does a loss of $1,000 hurt compared to the pleasure of a $1,000 gain?",
          ["Same amount", "Roughly twice as much", "Ten times as much", "Losses do not affect utility"], 1, "remember"),
        q("An investor refuses to sell a stock trading at $40 because they paid $60 for it six months ago, even though the company's fundamentals have deteriorated. Which bias is driving this behavior?",
          ["Confirmation bias", "Anchoring to purchase price", "Herding", "Recency bias"], 1, "apply"),
        q("In 2022, both stocks and bonds fell simultaneously, causing a traditional 60/40 portfolio to lose 16%. What portfolio theory assumption broke down?",
          ["Markets are efficient", "Stocks and bonds have low or negative correlation", "Diversification always reduces risk", "Bonds are risk-free"], 1, "analyze"),
        q("A systematic trading strategy buys stocks with strong recent returns. Which behavioral bias is this strategy indirectly exploiting?",
          ["Loss aversion", "Herding and momentum driven by recency bias", "Anchoring", "Overconfidence"], 1, "understand"),
        q("An advisor recommends a portfolio with 20% commodities, 15% managed futures, and 10% infrastructure alongside traditional stocks and bonds. How does this address MPT's limitations in 2026?",
          ["It increases fees", "Alternative assets provide uncorrelated returns that hedge against macro-driven correlation breakdowns", "Commodities always outperform stocks", "Managed futures replace bonds entirely"], 1, "evaluate"),
    ],
)

# ─── 3. Meta-Analysis & Statistical Literacy ────────────────────────────────
meta = make_entry(
    slug="learn/meta-analysis-statistics",
    title="Meta-Analysis & Statistical Literacy — Reading Research That Reads Research",
    description="Develop the skills to critically evaluate bodies of evidence: meta-analysis methods, effect sizes, p-value debates, Bayesian reasoning, and how the AcaciaFund SQI applies these principles.",
    body_html="""<p>Individual studies can mislead. Small samples produce false positives. p-hacking generates statistically significant but meaningless results. Publication bias distorts the evidence base. Meta-analysis — the statistical combination of results from multiple studies — is the most powerful tool we have for seeing through these distortions. Combined with statistical literacy, it forms the foundation of evidence-based research synthesis.</p>

<h2>Why Meta-Analysis Exists</h2>
<p>A single study with p = 0.04 and 30 participants may be a false positive. But if five independent labs each find a similar effect, the combined evidence is far more convincing. Meta-analysis formalizes this intuition: it <strong>pools</strong> effect sizes across studies, <strong>weights</strong> them by precision (inverse variance), and <strong>tests</strong> whether the overall effect is statistically significant and consistent across studies.</p>

<h2>Key Concepts</h2>
<ul>
<li><strong>Effect size:</strong> Standardized measure of the magnitude of a phenomenon (Cohen's d, Pearson's r, odds ratio). Unlike p-values, effect sizes tell you <em>how much</em> — not just <em>whether</em>.</li>
<li><strong>Heterogeneity:</strong> The degree to which study results differ beyond what chance would predict. High heterogeneity (I² > 75%) suggests the effect varies across contexts, populations, or methodologies — and a single summary estimate may be misleading.</li>
<li><strong>Funnel plot:</strong> A scatter plot of effect size vs. study precision. Asymmetry suggests publication bias: small studies with null results are missing (they were never published).</li>
<li><strong>Forest plot:</strong> The standard visualization showing each study's effect size and confidence interval, plus the meta-analytic summary (a diamond at the bottom).</li>
</ul>

<h2>The p-Value Debate</h2>
<p>The American Statistical Association's 2016 statement warned that p-values are widely misunderstood and misused. A p-value is <em>not</em> the probability that the null hypothesis is true. It is the probability of observing the data (or more extreme) assuming the null is true. By 2026, many journals have adopted <strong>stricter thresholds</strong> (p < 0.005 for "significant"), <strong>pre-registration requirements</strong>, and <strong>registered reports</strong> (peer review before results are known). The shift is toward effect sizes and confidence intervals as the primary reporting standard.</p>

<h2>Bayesian Reasoning for Research Synthesis</h2>
<p>Bayesian statistics offers an alternative framework that is more intuitive for research synthesis. Instead of a p-value, Bayes factors quantify the relative evidence for one hypothesis vs. another. A Bayes factor of 10 means the data are 10 times more likely under the alternative hypothesis than the null. Bayesian methods naturally incorporate prior information — crucial when combining results across studies where previous evidence informs current beliefs.</p>

<h2>The AcaciaFund SQI Connection</h2>
<p>The Signal Quality Index (SQI) applies meta-analytic thinking to news and research aggregation. It weights sources by authority (analogous to study quality), cross-source consensus (analogous to replication), freshness (analogous to recency), and relevance (analogous to applicability). Each AcaciaFund article's SQI is a meta-analytic summary of the evidence — not a single source's claim.</p>

<p>For the foundations of scientific reasoning, see <a href="/learn/science-method/">Scientific Reasoning in Research Synthesis</a>. The data pipeline that computes SQI at scale is explored in <a href="/learn/data-quality-engineering/">Data Quality Engineering</a>.</p>""",
    tags=["science", "statistics", "meta-analysis", "methodology", "replication", "bayesian", "research", "p-values"],
    pillar="science",
    difficulty="intermediate",
    flashcards=[
        {"term": "Effect Size", "definition": "A standardized measure of the magnitude of a phenomenon (Cohen's d, r, odds ratio) — more informative than p-values because it tells you how much, not just whether."},
        {"term": "Heterogeneity (I²)", "definition": "The proportion of observed variance in study results that reflects real differences rather than chance. I² > 75% indicates high heterogeneity."},
        {"term": "Funnel Plot", "definition": "A scatter plot of effect size vs. precision used to detect publication bias — asymmetry suggests small null-result studies are missing from the literature."},
        {"term": "Bayes Factor", "definition": "The ratio of the likelihood of the data under one hypothesis vs. another. BF > 3 suggests substantial evidence for the alternative; BF > 10 is strong."},
        {"term": "Registered Report", "definition": "A publication format where peer review occurs before results are known — study design and analysis plan are accepted in advance, reducing publication bias."},
    ],
    bloom_questions=[
        q("In a meta-analysis, what does high heterogeneity (I² = 85%) suggest about the combined results?",
          ["The summary effect is very precise", "Study results vary substantially beyond chance — the effect may differ across contexts", "The p-value is definitely significant", "No further analysis is needed"], 1, "understand"),
        q("A funnel plot shows most small studies cluster on the right (positive effect) side with very few on the left. What does this suggest?",
          ["The intervention is highly effective", "Publication bias — small null-result studies are missing from the literature", "Large studies are unreliable", "Heterogeneity is low"], 1, "analyze"),
        q("A study reports p = 0.03 with Cohen's d = 0.15 (very small effect) and N = 500. A second study reports p = 0.04 with d = 0.80 (large effect) and N = 30. Which finding should influence practice more?",
          ["The first — p is smaller", "The second — the effect size is much larger, despite the weaker p-value", "Neither — both are significant", "The first — it has a larger sample"], 1, "evaluate"),
        q("A Bayesian analysis returns a Bayes factor of 12 in favor of the alternative hypothesis. How should this be interpreted?",
          ["The alternative is 12 times more likely than the null given the data", "The p-value is 0.12", "The null hypothesis is rejected", "The effect size is 12"], 0, "remember"),
        q("How does the AcaciaFund SQI methodology reflect meta-analytic principles?",
          ["It only uses the most recent source", "It weights multiple sources by authority, cross-source consensus, freshness, and relevance — analogous to a meta-analysis weighting studies by quality", "It averages all p-values", "It ignores source quality"], 1, "apply"),
    ],
)

# ─── 4. Data Ethics & Privacy Engineering ──────────────────────────────────
data_ethics = make_entry(
    slug="learn/data-ethics-privacy",
    title="Data Ethics & Privacy Engineering — Building Trustworthy Data Systems",
    description="Navigate the ethical and privacy challenges of data-driven systems: privacy-by-design principles, differential privacy, consent management, AI ethics frameworks, and the 2026 regulatory landscape.",
    body_html="""<p>In 2026, 75% of the world's population lives in a jurisdiction with a comprehensive data protection law. AI regulation — the EU AI Act, US executive orders, China's AI regulations — is creating binding requirements for algorithmic transparency, fairness, and accountability. Data ethics is no longer a philosophical exercise; it is a compliance and engineering discipline.</p>

<h2>The Ethical Data Lifecycle</h2>
<p>Every stage of the data lifecycle carries ethical obligations:</p>
<ul>
<li><strong>Collection:</strong> Consent must be informed, specific, and revocable. Purpose limitation — data collected for one use cannot be arbitrarily repurposed. Minimization — collect only what is necessary.</li>
<li><strong>Storage:</strong> Encryption at rest and in transit. Access controls based on least privilege. Retention limits — delete data when the purpose is fulfilled.</li>
<li><strong>Processing:</strong> Fairness — algorithms must not discriminate based on protected characteristics. Transparency — subjects should know how their data is being used. Explainability — automated decisions must be explainable on request.</li>
<li><strong>Sharing:</strong> Data sharing agreements with clear use restrictions. Anonymization or pseudonymization before sharing. Audit trails for all data access and transfers.</li>
<li><strong>Deletion:</strong> Right to erasure (GDPR Article 17) — individuals can request deletion of their data. The engineering challenge is implementing deletion across distributed systems, backups, and ML training datasets.</li>
</ul>

<h2>Privacy-Enhancing Technologies (PETs)</h2>
<ul>
<li><strong>Differential Privacy:</strong> Adds calibrated noise to query results so that the presence or absence of any single individual's data does not meaningfully affect the output. Used by Apple (iOS analytics), Google (RAPPOR), and the US Census Bureau (2020 Census). The privacy parameter ε (epsilon) controls the trade-off: lower ε = more privacy, more noise, less accuracy.</li>
<li><strong>Federated Learning:</strong> ML models are trained across decentralized data sources without raw data leaving each source. Only model updates (gradients) are shared, not the underlying data. Used by Google (Gboard keyboard suggestions), Apple (Siri), and healthcare consortia.</li>
<li><strong>Synthetic Data:</strong> Artificially generated data that preserves the statistical properties of the original dataset without containing identifiable records. Increasingly used for ML training, testing, and sharing when real data cannot be distributed.</li>
<li><strong>Homomorphic Encryption:</strong> Computation on encrypted data — the data never needs to be decrypted for processing. Computationally expensive but rapidly improving; used in healthcare and financial services for secure multi-party computation.</li>
</ul>

<h2>AI Ethics & Regulation in 2026</h2>
<p>The EU AI Act (effective 2025-2026) classifies AI systems by risk level: unacceptable (banned), high-risk (conformity assessment required), limited (transparency obligations), and minimal (voluntary codes). High-risk systems include credit scoring, hiring, law enforcement, and biometric identification. Requirements include: risk management, data governance, transparency, human oversight, and accuracy/robustness standards. The US has taken a sectoral approach with executive orders on AI safety and agency-specific guidance, while China requires algorithm filing and approval for recommendation and synthesis algorithms.</p>

<h2>Consent Management</h2>
<p>Consent is the legal basis for most data processing, but the 2026 standard has moved beyond the "cookie banner" era. Key principles: <strong>granularity</strong> (separate consents for different purposes), <strong>affirmative action</strong> (pre-ticked boxes are illegal under GDPR), <strong>easy withdrawal</strong> (revocation must be as easy as granting), and <strong>continuous consent</strong> (consent expires and must be refreshed periodically). Consent Management Platforms (CMPs) have become standard infrastructure, integrated via the IAB Transparency & Consent Framework.</p>

<p>For the data pipeline infrastructure that must implement these privacy controls, see <a href="/learn/dataops-introduction/">Introduction to DataOps</a> and <a href="/learn/open-source-data-stack/">Building an Open Source Data Stack</a>.</p>""",
    tags=["ethics", "privacy", "gdpr", "ai-act", "differential-privacy", "consent", "regulation", "dataops", "security"],
    pillar="stock",
    difficulty="advanced",
    flashcards=[
        {"term": "Differential Privacy", "definition": "A mathematical framework that adds calibrated noise to query results so that the presence of any single individual's data does not meaningfully affect the output."},
        {"term": "Federated Learning", "definition": "A machine learning technique where models are trained across decentralized data sources without raw data leaving each source — only model updates are shared."},
        {"term": "EU AI Act", "definition": "The European Union's comprehensive AI regulation (effective 2025-2026), classifying AI systems by risk level with binding requirements for high-risk systems."},
        {"term": "GDPR Article 17", "definition": "The Right to Erasure ('Right to be Forgotten') — individuals can request deletion of their personal data, creating engineering challenges for distributed systems."},
        {"term": "Synthetic Data", "definition": "Artificially generated data preserving the statistical properties of an original dataset without containing identifiable records — used when real data cannot be shared."},
    ],
    bloom_questions=[
        q("A company collects user location data for product recommendations and later uses the same data for insurance risk scoring without informing users. Which ethical principle is violated?",
          ["Data minimization", "Purpose limitation", "Storage limitation", "Right to erasure"], 1, "understand"),
        q("A health research consortium wants to train a diagnostic ML model across 50 hospitals without any hospital sharing patient data externally. Which PET should they use?",
          ["Differential privacy", "Federated learning", "Homomorphic encryption", "Synthetic data"], 1, "apply"),
        q("The US Census Bureau adds noise to published demographic statistics so that no individual's responses can be inferred. This is an implementation of:",
          ["Federated learning", "Differential privacy (low ε, high noise)", "Homomorphic encryption", "k-anonymity"], 1, "remember"),
        q("An AI-powered hiring system automatically rejects 70% of female applicants. Under the EU AI Act, what obligations apply?",
          ["No obligations — hiring AI is exempt", "The system is high-risk, requiring conformity assessment, bias testing, and human oversight", "Only transparency labeling is required", "The system must be trained on more male applicants"], 1, "evaluate"),
        q("A data engineer implements differential privacy with ε = 10 (high utility, low privacy). Regulators require stronger privacy guarantees. What should the engineer do?",
          ["Increase ε to 100", "Decrease ε to 1 or lower, accepting reduced accuracy in exchange for stronger privacy protection", "Switch to homomorphic encryption", "Disable the privacy mechanism"], 1, "evaluate"),
    ],
)

# ─── Add to registry ────────────────────────────────────────────────────────
new_lessons = [tbml, behav_fin, meta, data_ethics]
for lesson in new_lessons:
    if lesson["slug"] not in existing_slugs:
        registry["content"].append(lesson)
        print(f"  Added: {lesson['slug']}")
    else:
        print(f"  Skipped (exists): {lesson['slug']}")

with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

print("\nCurriculum summary:")
for c in registry["content"]:
    if c.get("content_type") == "learn":
        bq = len(c.get("bloom_questions", []))
        fc = len(c.get("flashcards", []))
        body = len(c.get("body_html", "") or "")
        print(f"  {c['slug']:40s} body={body:>5}  fc={fc}  bq={bq}  diff={c.get('difficulty','?'):12s}  pillar={c.get('pillar','?')}")
