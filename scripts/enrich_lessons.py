"""Enrich all learn lessons with full content, flashcards, quiz questions, and cross-references."""
import json

REGISTRY_PATH = "registry.json"
with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    registry = json.load(f)

entries = {c["slug"]: c for c in registry["content"]}

def q(question, options, answer, bloom_level="understand"):
    return {
        "bloom_level": bloom_level,
        "type": "mc",
        "question": question,
        "options": options,
        "answer": answer,
    }

# ─── 1. learn/aml-basics ───────────────────────────────────────────────────
entries["learn/aml-basics"].update({
    "body_html": """<p>Money laundering is the process of making illegally obtained funds appear legitimate. Each year, an estimated $800 billion to $2 trillion is laundered globally — roughly 2–5% of global GDP. Understanding how this works and how to counter it is the foundation of financial crime compliance.</p>

<h2>What is Money Laundering?</h2>
<p>Money laundering transforms "dirty money" (proceeds from crime) into "clean money" that can be used without raising suspicion. The activity is not a single event but a three-stage process designed to sever the link between the crime and the funds.</p>

<h2>The Three Stages</h2>
<h3>1. Placement</h3>
<p>The launderer introduces illicit funds into the financial system. This is the most vulnerable stage — large cash deposits, foreign wire transfers, or purchasing high-value assets (real estate, art, luxury goods). Banks use <strong>Currency Transaction Reports (CTRs)</strong> and <strong>Suspicious Activity Reports (SARs)</strong> to flag unusual patterns.</p>

<h3>2. Layering</h3>
<p>The funds are moved through complex transactions to obscure the audit trail. Typical layering techniques include: wiring money through multiple accounts in different jurisdictions, trading through shell companies, over-invoicing trade transactions, and using cryptocurrency mixers. Layering is the hardest stage to detect because the transactions often appear legitimate in isolation.</p>

<h3>3. Integration</h3>
<p>The now-cleaned funds re-enter the legitimate economy. The launderer can spend, invest, or hold the money openly. At this stage, the funds are indistinguishable from legitimate wealth, making prosecution extremely difficult unless the earlier stages were documented.</p>

<h2>The AML Regulatory Framework</h2>
<p>Anti-Money Laundering (AML) regulations require financial institutions to implement three lines of defense:</p>
<ul>
<li><strong>Know Your Customer (KYC):</strong> Verify customer identity, understand the nature of their business, and assess risk level before onboarding.</li>
<li><strong>Transaction Monitoring:</strong> Screen all transactions against watchlists, sanctions lists, and behavioral baselines to detect suspicious patterns.</li>
<li><strong>Reporting:</strong> File Suspicious Activity Reports (SARs) with financial intelligence units when red flags are triggered.</li>
</ul>
<p>The Financial Action Task Force (FATF) sets global AML standards, which are implemented locally by regulators such as FinCEN (US), the FCA (UK), and the European Banking Authority.</p>

<h2>Red Flags in Practice</h2>
<p>Common AML red flags include: structuring deposits just below reporting thresholds ($10,000 in the US), rapid movement of funds through unrelated accounts, transactions inconsistent with the customer's known business, and customers from high-risk jurisdictions without economic rationale. Machine learning models now supplement rule-based systems by detecting subtle, non-obvious patterns that would escape manual review.</p>

<p>In the next lesson — <a href="/learn/quiz-aml/">AML Knowledge Check</a> — you can test your understanding of these concepts with interactive quiz questions.</p>""",
    "description": "Understand money laundering stages, the AML regulatory framework, KYC requirements, suspicious activity red flags, and real-world detection techniques.",
    "tags": ["aml", "money-laundering", "kyc", "regulations", "compliance", "financial-crime"],
    "flashcards": [
        {"term": "Placement", "definition": "The first stage of money laundering — introducing illicit funds into the financial system through deposits, purchases, or wire transfers."},
        {"term": "Layering", "definition": "The second stage — moving funds through complex, often cross-border transactions to obscure the audit trail from law enforcement."},
        {"term": "Integration", "definition": "The final stage — re-introducing laundered funds into the legitimate economy so they appear to be lawful income."},
        {"term": "SAR", "definition": "Suspicious Activity Report — a confidential filing financial institutions submit to regulators when they detect potentially suspicious transactions."},
        {"term": "FATF", "definition": "Financial Action Task Force — the intergovernmental body that sets global AML standards and coordinates counter-measures among member countries."},
    ],
    "bloom_questions": [
        q("What is the most vulnerable stage of money laundering from the launderer's perspective?",
          ["Placement", "Layering", "Integration", "None of the above"], 0, "remember"),
        q("Which document do US banks file when a customer deposits more than $10,000 in cash?",
          ["Suspicious Activity Report (SAR)", "Currency Transaction Report (CTR)", "Know Your Customer (KYC) Form", "Financial Action Task Force (FATF) Report"], 1, "remember"),
        q("A launderer wires money through shell companies in three different countries. This is an example of which stage?",
          ["Placement", "Layering", "Integration", "Structuring"], 1, "apply"),
        q("Why is the integration stage difficult to prosecute?",
          ["The funds are held in offshore accounts", "The funds are indistinguishable from legitimate wealth", "Banks cannot file SARs at this stage", "FATF regulations do not cover integration"], 1, "analyze"),
        q("Which of the following is a common AML red flag?",
          ["A customer deposits exactly $9,900 weekly", "A corporation files quarterly tax returns", "A retail store accepts credit cards", "An employee contributes to a retirement account"], 0, "understand"),
    ],
})

# ─── 2. learn/quiz-aml ────────────────────────────────────────────────────
entries["learn/quiz-aml"].update({
    "body_html": """<p>Now that you've completed <a href="/learn/aml-basics/">AML Fundamentals</a>, test your knowledge with these scenario-based questions. Each question presents a real-world situation drawn from regulatory guidelines, enforcement actions, or compliance best practices.</p>

<h2>About This Assessment</h2>
<p>This quiz covers the three stages of money laundering, the AML regulatory framework, suspicious activity indicators, and the role of technology in detection. Questions progress from recall (remembering definitions) to application (analyzing scenarios).</p>
<p>Use the interactive quiz below to check your understanding. Each question includes an explanation after you select an answer, so even incorrect responses become learning opportunities.</p>

<h2>Review Before You Start</h2>
<p>Key concepts to refresh: the difference between <strong>placement</strong>, <strong>layering</strong>, and <strong>integration</strong>; the purpose of <strong>KYC</strong> and <strong>SAR</strong> filings; common <strong>red flags</strong> like structuring and rapid fund movements; and the role of <strong>FATF</strong> in setting international standards.</p>

<p>Ready? The interactive assessment is below. For deeper study, explore the <a href="/knowledge/glossary/">AML Glossary</a> in the Knowledge Base.</p>""",
    "description": "Scenario-based quiz testing AML knowledge across money laundering stages, regulations, red flag detection, and compliance practices — paired with the AML Fundamentals lesson.",
    "tags": ["aml", "quiz", "assessment", "knowledge-check", "compliance"],
    "flashcards": [
        {"term": "Structuring", "definition": "The practice of breaking large transactions into smaller amounts to avoid reporting thresholds — a key indicator of money laundering activity."},
        {"term": "Beneficial Ownership", "definition": "The natural person who ultimately owns or controls a legal entity — uncovering this is a major focus of modern AML regulations."},
        {"term": "PEP", "definition": "Politically Exposed Person — an individual with a prominent public role who poses higher corruption risk and requires enhanced due diligence."},
    ],
    "bloom_questions": [
        q("A customer makes three cash deposits of $9,000 each at different bank branches on the same day. What is this called?",
          ["Placement", "Structuring", "Layering", "Smurfing"], 1, "apply"),
        q("Which regulatory body sets the global standards that national AML laws are built upon?",
          ["FinCEN", "FCA", "FATF", "IMF"], 2, "remember"),
        q("A real estate developer accepts cryptocurrency for a luxury property sale but the buyer's identity cannot be verified. What AML obligation applies?",
          ["No obligation if crypto is used", "File a SAR if suspicious activity is suspected", "Only file CTR for cash equivalents", "Report to the local tax authority"], 1, "evaluate"),
        q("What is the primary purpose of the Layering stage?",
          ["To deposit cash into a bank account", "To obscure the audit trail through complex transactions", "To spend laundered funds on legitimate assets", "To file required regulatory reports"], 1, "understand"),
        q("A bank's transaction monitoring system flags a customer account that received 47 small wire transfers from 12 different countries in 24 hours. What should happen next?",
          ["Nothing — wires from multiple countries are normal", "Automatically freeze the account", "Investigate and file a SAR if warranted", "Report to the customer's employer"], 2, "evaluate"),
    ],
})

# ─── 3. learn/market-analysis ─────────────────────────────────────────────
entries["learn/market-analysis"].update({
    "body_html": """<p>Market signals are data points that reflect the health, direction, and sentiment of financial markets. Being able to read these signals — and distinguish genuine trends from noise — is an essential skill for investors, analysts, and anyone working at the intersection of finance and data.</p>

<h2>Types of Market Signals</h2>

<h3>Fundamental Signals</h3>
<p>Fundamental analysis evaluates a company's intrinsic value. Key signals include: <strong>earnings reports</strong> (revenue growth, EPS beats/misses), <strong>P/E ratios</strong> relative to sector averages, <strong>debt-to-equity</strong> ratios signaling financial health, and <strong>free cash flow</strong> trends. A stock's price eventually follows its fundamentals — but the timing can be unpredictable.</p>

<h3>Technical Signals</h3>
<p>Technical analysis studies price and volume patterns. Common technical signals: <strong>moving average crossovers</strong> (e.g., 50-day crossing above 200-day = "golden cross"), <strong>RSI (Relative Strength Index)</strong> above 70 (overbought) or below 30 (oversold), <strong>volume spikes</strong> confirming breakouts, and <strong>support/resistance levels</strong> where price has historically reversed.</p>

<h3>Sentiment Signals</h3>
<p>Sentiment analysis measures the market's emotional state. Sources include: <strong>VIX</strong> (fear index), put/call ratios, short interest percentages, social media sentiment from financial forums like r/WallStreetBets, and news tone analysis from financial newswires. These signals are especially useful for identifying contrarian opportunities.</p>

<h3>Macroeconomic Signals</h3>
<p>Broad economic indicators that move entire markets: <strong>interest rate decisions</strong> by central banks, <strong>CPI / PPI</strong> inflation data, <strong>unemployment claims</strong>, <strong>GDP growth</strong> rates, and <strong>purchasing managers' index (PMI)</strong> data. These signals often override company-level fundamentals during periods of economic transition.</p>

<h2>Signal vs. Noise</h2>
<p>The biggest challenge in market analysis is distinguishing signal from noise. A single earnings beat does not make a trend; a single down day does not make a crash. Analysts use statistical techniques like <strong>moving averages</strong>, <strong>Bollinger Bands</strong> (2 standard deviations from the mean), and <strong>correlation analysis</strong> to filter noise. The AcaciaFund SQI methodology applies similar filtering — weighting source authority, freshness, and consensus — to synthesize reliable investment theses.</p>

<h2>Building a Signal Dashboard</h2>
<p>A practical signal dashboard might track: 10-year Treasury yield (macro), VIX (sentiment), sector ETF performance (relative strength), top 10 holdings earnings dates (fundamental), and a custom momentum factor combining RSI and volume trends. The key is to define <em>what action each signal triggers</em> before the signal appears, not after.</p>

<p>To explore the data engineering behind market signal processing, see <a href="/learn/dataops-introduction/">Introduction to DataOps</a> — the first lesson in our data pipeline track.</p>""",
    "description": "Learn to identify and interpret fundamental, technical, sentiment, and macroeconomic market signals — and distinguish genuine trends from noise.",
    "tags": ["markets", "stock", "technical-analysis", "fundamental-analysis", "trading", "signals"],
    "flashcards": [
        {"term": "Golden Cross", "definition": "A bullish technical signal where a short-term moving average (e.g., 50-day) crosses above a long-term moving average (e.g., 200-day)."},
        {"term": "RSI", "definition": "Relative Strength Index — a momentum oscillator measuring the speed and magnitude of recent price changes, ranging 0-100 with overbought above 70 and oversold below 30."},
        {"term": "VIX", "definition": "CBOE Volatility Index — the market's expectation of 30-day forward volatility, often called the 'fear index'."},
        {"term": "Bollinger Bands", "definition": "Volatility bands placed 2 standard deviations above and below a moving average — prices touching the bands suggest overbought or oversold conditions."},
        {"term": "PMI", "definition": "Purchasing Managers' Index — a survey-based economic indicator measuring manufacturing and services sector activity, with values above 50 indicating expansion."},
    ],
    "bloom_questions": [
        q("Which type of market signal would a VIX reading above 30 typically represent?",
          ["Fundamental signal", "Technical signal", "Sentiment signal", "Macroeconomic signal"], 2, "remember"),
        q("A stock's 50-day moving average crosses above its 200-day moving average. What is this signal called?",
          ["Death Cross", "Golden Cross", "RSI Divergence", "Breakout Confirmation"], 1, "understand"),
        q("A company reports earnings that beat analyst estimates by 15%, yet its stock price drops 4% the same day. How might an analyst reconcile this?",
          ["The market is irrational", "The beat was already priced in, and forward guidance was weak", "Technical signals override fundamentals", "Short sellers manipulated the price"], 1, "analyze"),
        q("An analyst wants to build a dashboard that triggers a buy signal only when three independent sources agree. Which statistical approach helps filter noise?",
          ["Bollinger Bands", "Correlation analysis across multiple signals", "RSI divergence detection", "Simple moving average"], 1, "apply"),
        q("Why might a sentiment signal like social media bullishness be a contrarian indicator?",
          ["Social media users are always wrong", "Extreme bullish sentiment often precedes market tops", "Sentiment signals are always lagging", "Contrarian trading is the only profitable strategy"], 1, "evaluate"),
    ],
})

# ─── 4. learn/science-method ──────────────────────────────────────────────
entries["learn/science-method"].update({
    "body_html": """<p>Scientific reasoning is the foundation of reliable research synthesis. In an era of information overload — where a single study can go viral before it is peer-reviewed — the ability to evaluate claims critically is more important than ever. This lesson equips you with the tools to assess scientific evidence, understand methodological pitfalls, and apply structured reasoning to research analysis.</p>

<h2>The Scientific Method in Research Synthesis</h2>
<p>The traditional scientific method — hypothesis, experiment, analysis, conclusion — maps directly onto research synthesis. The AcaciaFund pipeline applies this cycle: we <strong>hypothesize</strong> which sources carry signal, <strong>ingest and analyze</strong> content from HackerNews and arXiv, <strong>evaluate</strong> quality via SQI metrics, and <strong>conclude</strong> with synthesized findings organized by Bloom taxonomy level.</p>

<h2>Understanding the Replication Crisis</h2>
<p>Across psychology, biomedicine, and economics, large-scale replication efforts have found that 30–60% of published studies fail to replicate. Causes include: <strong>p-hacking</strong> (running analyses until a significant p-value appears), <strong>small sample sizes</strong> producing false positives, <strong>publication bias</strong> favoring positive results, and <strong>questionable research practices</strong> like selective reporting. The replication crisis underscores why single studies should never be taken as definitive truth — and why synthesis across multiple sources is essential.</p>

<h2>Applying Bloom Taxonomy to Research</h2>
<p>The Bloom taxonomy classifies cognitive skills across six levels:</p>
<ul>
<li><strong>Remember:</strong> Recall facts, definitions, and basic concepts from the source.</li>
<li><strong>Understand:</strong> Explain the meaning and implications of the findings.</li>
<li><strong>Apply:</strong> Use the knowledge in a new context or scenario.</li>
<li><strong>Analyze:</strong> Break down the argument — identify assumptions, evidence, and logical structure.</li>
<li><strong>Evaluate:</strong> Judge the quality, credibility, and relevance of the research.</li>
<li><strong>Create:</strong> Synthesize insights into new frameworks, hypotheses, or approaches.</li>
</ul>
<p>When reading a research article, try to classify each claim by Bloom level. This practice sharpens your ability to distinguish between descriptive summaries and analytical insights.</p>

<h2>Practical Heuristics for Evaluating Claims</h2>
<ul>
<li><strong>Effect size matters more than p-value:</strong> A statistically significant result with a tiny effect may be meaningless in practice.</li>
<li><strong>Sample size and power:</strong> Studies with fewer than 100 participants per group should be treated with caution unless effects are very large.</li>
<li><strong>Pre-registration:</strong> Studies that pre-register their analysis plan are less likely to produce false positives than those that don't.</li>
<li><strong>Source diversity:</strong> Findings replicated across different labs, methods, and populations are substantially more trustworthy than single-site results.</li>
</ul>
<p>The AcaciaFund SQI incorporates these heuristics directly — weighting source authority, methodological rigor, and cross-source consensus into every quality score.</p>

<p>For a practical application of these concepts, explore <a href="/learn/data-quality-engineering/">Data Quality Engineering</a>, which shows how scientific testing principles extend to data pipelines.</p>""",
    "description": "Master the skills of scientific reasoning: evaluating claims, understanding replication crisis, applying Bloom taxonomy to research synthesis, and using practical heuristics for evidence assessment.",
    "tags": ["science", "methodology", "reasoning", "bloom-taxonomy", "replication", "research"],
    "flashcards": [
        {"term": "P-Hacking", "definition": "Running multiple statistical analyses or stopping data collection at convenient points until a significant p-value (<0.05) is found, inflating false positive rates."},
        {"term": "Publication Bias", "definition": "The tendency for journals to publish positive or novel results while rejecting null findings, distorting the published evidence base."},
        {"term": "Effect Size", "definition": "A quantitative measure of the magnitude of a phenomenon, independent of sample size — more informative than p-values alone for assessing practical significance."},
        {"term": "Pre-registration", "definition": "Publicly documenting a study's hypothesis, methodology, and analysis plan before data collection begins, reducing the risk of p-hacking and selective reporting."},
        {"term": "SQI", "definition": "Signal Quality Index — a composite metric measuring source authority, freshness, cross-source consensus, and relevance, used by AcaciaFund to score research reliability."},
    ],
    "bloom_questions": [
        q("Why does publication bias threaten the reliability of published research?",
          ["Journals charge high subscription fees", "Null results are less likely to be published, skewing the evidence base", "Peer review is not rigorous enough", "Researchers do not share their data"], 1, "understand"),
        q("A study reports p = 0.04 with 20 participants per group and a very small effect size. How should you evaluate this claim?",
          ["Accept it — p < 0.05 means it is true", "Treat with caution — small sample + small effect = likely false positive", "Ignore reporting standards entirely", "Reject — only large sample studies are valid"], 1, "evaluate"),
        q("Which Bloom taxonomy level involves breaking down an argument to identify assumptions and logical structure?",
          ["Remember", "Understand", "Apply", "Analyze"], 3, "remember"),
        q("A finding has been replicated across five independent labs using different methodologies. Compared to a single-site study, this replication:",
          ["Is equally trustworthy", "Is more trustworthy due to methodological diversity", "Is less trustworthy due to inconsistency", "Cannot be compared"], 1, "evaluate"),
        q("What is the key difference between an 'apply' level question and an 'analyze' level question?",
          ["Apply is harder than analyze", "Apply uses knowledge in a new scenario; analyze breaks down structure and assumptions", "Apply is for science; analyze is for math", "There is no meaningful difference"], 1, "understand"),
    ],
})

# ─── 5. learn/dataops-introduction ─────────────────────────────────────────
entries["learn/dataops-introduction"].update({
    "tags": ["best-practices", "pipeline", "stock", "dataops", "data-engineering", "orchestration", "ci-cd"],
    "bloom_questions": [
        q("What is the primary unit of work in DataOps?",
          ["Code commit", "Data pipeline run", "Model training run", "Database query"], 1, "remember"),
        q("A pipeline manifest file should declare all of the following EXCEPT:",
          ["Source connectors and schemas", "Data quality expectations per stage", "Employee salaries", "SLOs for freshness and completeness"], 2, "understand"),
        q("A data team notices row counts dropped 40% overnight. Which DataOps principle is most directly relevant?",
          ["Reproducibility", "Pipeline Observability", "Version Everything", "Continuous Delivery"], 1, "apply"),
        q("How does the Medallion Architecture (Bronze → Silver → Gold) support DataOps quality goals?",
          ["It adds more storage layers", "Each layer applies increasing quality standards, catching errors early", "It replaces the need for data quality checks", "It only works with Delta Lake"], 1, "analyze"),
        q("Your organization wants to move from a monolithic data platform to a modular open source stack. What is the first quality gate you should implement?",
          ["Deploy an ML model", "Define data quality expectations on incoming source data", "Build a dashboard first", "Migrate all data to the cloud"], 1, "evaluate"),
    ],
})

# ─── 6. learn/data-quality-engineering ─────────────────────────────────────
entries["learn/data-quality-engineering"].update({
    "tags": ["engineering", "stock", "dataops", "testing", "data-quality", "expectations", "monitoring"],
    "bloom_questions": [
        q("Which data quality layer checks whether all expected records are present in a dataset?",
          ["Freshness", "Completeness", "Accuracy", "Consistency"], 1, "remember"),
        q("A pipeline stops execution when a Great Expectations check fails. This is an example of:",
          ["Soft gate", "Hard gate", "Schema drift", "Observability"], 1, "understand"),
        q("Your data pipeline suddenly shows 0% null rate on a column that previously had 5% nulls. How should you interpret this?",
          ["Data quality has improved", "Likely a schema change or silent failure in the source", "Ignore — null rates naturally fluctuate", "Increase the threshold to 10%"], 1, "analyze"),
        q("You need to detect when new columns appear unexpectedly in a production dataset. Which tool category is most appropriate?",
          ["Data orchestration (Dagster/Airflow)", "Schema monitoring (part of data quality framework)", "Data integration (Airbyte/Meltano)", "Business intelligence (Metabase/Superset)"], 1, "apply"),
        q("An engineering team defines 200 expectations but never reviews the results. What data quality anti-pattern is this?",
          ["Over-testing", "Alert fatigue from unchecked monitoring", "Expectation drift", "Silent failure of quality gates"], 1, "evaluate"),
    ],
})

# ─── 7. learn/open-source-data-stack ───────────────────────────────────────
entries["learn/open-source-data-stack"].update({
    "tags": ["architecture", "open-source", "data-stack", "stock", "dataops", "lakehouse", "ingestion"],
    "bloom_questions": [
        q("Which layer of the open source data stack does Apache Iceberg belong to?",
          ["Ingestion", "Storage", "Transformation", "Orchestration"], 1, "remember"),
        q("What distinguishes Dagster from Airflow in data pipeline orchestration?",
          ["Dagster uses Python; Airflow uses SQL", "Dagster treats datasets as assets with explicit lineage; Airflow focuses on task DAGs", "Airflow is open source; Dagster is proprietary", "Dagster cannot run on Kubernetes"], 1, "understand"),
        q("A team needs to migrate from a monolithic data warehouse to a lakehouse architecture. Which two tools form the core of the new stack?",
          ["dbt + Airbyte", "Iceberg + Trino", "Kafka + Flink", "Metabase + Superset"], 1, "apply"),
        q("Why is a lakehouse architecture preferred over a traditional data warehouse for modern data teams?",
          ["Lakehouses are cheaper but slower", "Lakehouses combine data lake flexibility with warehouse ACID guarantees", "Lakehouses require less engineering talent", "Lakehouses only work with structured data"], 1, "analyze"),
        q("Your VP asks for a 'zero licensing fee' production data stack serving 50 analysts. What is the most critical cost not captured by tool licensing?",
          ["Cloud compute and storage costs", "Engineering time for integration and maintenance", "Both cloud infrastructure and engineering time", "Data quality tool costs"], 2, "evaluate"),
    ],
})

# ─── Write back ────────────────────────────────────────────────────────────
with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

print("Done. Updated all learn lessons with quizzes, content, and cross-references.")

# Quick summary
for c in registry["content"]:
    if c.get("content_type") == "learn":
        bq = c.get("bloom_questions", [])
        fc = c.get("flashcards", [])
        body = c.get("body_html", "") or ""
        print(f"  {c['slug']:40s} body={len(body):>5}  fc={len(fc)}  bq={len(bq)}  diff={c.get('difficulty','?')}")
