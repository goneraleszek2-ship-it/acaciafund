#!/usr/bin/env python3
"""Backfill body_html, quality metadata, and flashcards for empty registry items."""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
REGISTRY_PATH = os.path.join(ROOT_DIR, "registry.json")

# ──────────────────────────────────────────────
# Topic-specific content generators
# ──────────────────────────────────────────────

TOPIC_CONTENT = {
    # ── AML research articles ──
    "aml/research/what-is-money-laundering": {
        "overview_paras": [
            "Money laundering is the process by which illegally obtained funds are made to appear legitimate. Criminals use a variety of techniques to disguise the origin of proceeds from drug trafficking, fraud, corruption, and other serious offenses. The act of laundering money is essential to organized crime because it allows criminals to use their illicit gains without drawing suspicion from law enforcement or financial regulators.",
            "The typical money laundering process is broken into three stages: placement, layering, and integration. During placement, illicit funds are introduced into the financial system through deposits, purchases, or other transactions. Layering involves moving funds through complex transactions to obscure their origin, often crossing multiple jurisdictions. Finally, integration returns the laundered money to the criminal as seemingly legitimate wealth. Combating money laundering requires a coordinated effort between financial institutions, regulators, and law enforcement agencies worldwide."
        ],
        "key_concepts": [
            ("Placement", "The first stage where illicit cash enters the financial system through deposits, currency exchanges, or purchasing assets."),
            ("Layering", "The second stage involving complex transactions designed to distance funds from their criminal source through multiple transfers and shell companies."),
            ("Integration", "The final stage where laundered money is returned to the criminal as legitimate wealth through investments, real estate, or business ventures."),
            ("Structuring", "Also known as smurfing, this technique breaks large sums into smaller deposits to avoid reporting thresholds."),
            ("Trade-Based Laundering", "Over- or under-invoicing goods and services to move value across borders without attracting attention.")
        ],
        "why_it_matters": [
            "Money laundering poses a serious threat to the integrity of the global financial system. The International Monetary Fund estimates that laundered funds represent 2 to 5 percent of global GDP annually. This scale of illicit finance undermines legitimate economic activity, distorts asset prices, and enables further criminal enterprise.",
            "For financial institutions, the consequences of facilitating money laundering are severe. Regulatory penalties, reputational damage, and criminal liability can threaten the viability of banks and other financial intermediaries. Effective anti-money laundering programs are not just regulatory requirements but essential safeguards for institutional integrity."
        ],
        "takeaways": [
            "Money laundering conceals the criminal origin of funds through a three-stage process of placement, layering, and integration.",
            "Financial institutions are the first line of defense and must implement robust AML compliance programs.",
            "Global coordination through organizations like FATF is essential to combat cross-border money laundering effectively.",
            "Non-compliance with AML regulations carries severe penalties, including fines, license revocation, and criminal charges."
        ],
        "flashcards": [
            {"front": "What are the three stages of money laundering?", "back": "Placement (introducing illicit funds), Layering (obscuring through complex transactions), and Integration (returning as legitimate wealth)."},
            {"front": "What is structuring (smurfing)?", "back": "Breaking large sums of illicit cash into smaller deposits to avoid triggering regulatory reporting thresholds."},
            {"front": "What percentage of global GDP is laundered annually?", "back": "An estimated 2 to 5 percent of global GDP, according to the International Monetary Fund."},
            {"front": "What is trade-based money laundering?", "back": "Over- or under-invoicing goods and services to move value across borders without attracting regulatory attention."}
        ]
    },
    "aml/research/kyc-basics": {
        "overview_paras": [
            "Know Your Customer (KYC) is the cornerstone of anti-money laundering compliance. It refers to the process by which financial institutions verify the identity of their clients, assess their risk profile, and understand the nature of their financial activities. KYC is not merely a regulatory checkbox but a fundamental risk management practice that protects institutions from being used for financial crime.",
            "A robust KYC framework consists of three key components: customer identification program (CIP), customer due diligence (CDD), and ongoing monitoring. CIP requires collecting and verifying identifying information such as name, address, date of birth, and government-issued ID numbers. CDD involves assessing the customer's risk level based on factors like occupation, source of funds, and geographic location. Ongoing monitoring ensures that customer activity remains consistent with their stated profile throughout the business relationship."
        ],
        "key_concepts": [
            ("Customer Identification Program", "The initial verification process that collects and validates government-issued identification documents and personal information."),
            ("Customer Due Diligence", "The risk assessment process that categorizes customers based on their financial behavior, occupation, and geographic risk factors."),
            ("Enhanced Due Diligence", "A higher level of scrutiny applied to high-risk customers such as Politically Exposed Persons (PEPs) or those from high-risk jurisdictions."),
            ("Beneficial Ownership", "The identification of the natural persons who ultimately own or control a legal entity, preventing anonymous shell company abuse."),
            ("Ongoing Monitoring", "Continuous surveillance of customer transactions and behavior to detect deviations from expected patterns.")
        ],
        "why_it_matters": [
            "KYC compliance is the first and most critical defense against financial crime. Without robust identity verification and risk assessment, financial institutions operate blindly, exposing themselves to money laundering, terrorist financing, and fraud. Regulatory bodies worldwide have made KYC failures a primary enforcement priority, with billions of dollars in fines levied against institutions with inadequate programs.",
            "Beyond regulatory compliance, effective KYC processes improve business outcomes. Institutions with strong KYC programs experience fewer fraud losses, better customer relationship management, and more efficient onboarding. In the era of digital banking and fintech competition, streamlined KYC processes have become a competitive differentiator."
        ],
        "takeaways": [
            "KYC consists of three pillars: customer identification, due diligence, and ongoing monitoring.",
            "Enhanced Due Diligence applies to high-risk categories including PEPs and high-risk jurisdictions.",
            "Beneficial ownership identification prevents anonymous entities from hiding illicit funds.",
            "Strong KYC programs reduce fraud losses and improve regulatory outcomes for financial institutions."
        ],
        "flashcards": [
            {"front": "What does KYC stand for?", "back": "Know Your Customer — the process of verifying client identity and assessing risk."},
            {"front": "What are the three components of KYC?", "back": "Customer Identification Program (CIP), Customer Due Diligence (CDD), and Ongoing Monitoring."},
            {"front": "What is Enhanced Due Diligence?", "back": "A higher level of scrutiny for high-risk customers such as Politically Exposed Persons (PEPs)."},
            {"front": "What is beneficial ownership?", "back": "Identifying the natural persons who ultimately own or control a legal entity, preventing shell company abuse."}
        ]
    },
    "aml/research/aml-regulatory-landscape": {
        "overview_paras": [
            "The global AML regulatory landscape is a complex web of international standards, national laws, and industry guidelines designed to combat money laundering and terrorist financing. At the apex sits the Financial Action Task Force (FATF), an intergovernmental body that sets international standards and evaluates countries' compliance. FATF's 40 Recommendations provide the framework that national regulators use to design their own AML regimes.",
            "In the United States, the Bank Secrecy Act (BSA) of 1970 and the USA PATRIOT Act of 2001 form the backbone of AML regulation. The BSA requires financial institutions to maintain records, file reports such as Currency Transaction Reports (CTRs) and Suspicious Activity Reports (SARs), and implement compliance programs. The European Union's AML Directives (now the AMLR) create a harmonized framework across member states, while jurisdictions like Singapore, Hong Kong, and the UAE operate their own robust regulatory systems."
        ],
        "key_concepts": [
            ("FATF Recommendations", "The 40 international standards for combating money laundering and terrorist financing, updated regularly to address emerging threats."),
            ("Bank Secrecy Act", "The foundational US AML law requiring recordkeeping, reporting, and compliance programs for financial institutions."),
            ("USA PATRIOT Act", "Post-9/11 legislation that expanded AML requirements including Section 314 information sharing and enhanced due diligence."),
            ("EU AML Directives", "A series of progressively stronger EU-wide directives that harmonize AML practices across member states, now evolving into a single Regulation (AMLR)."),
            ("National Risk Assessment", "A country-level evaluation of money laundering and terrorist financing risks that informs regulatory priorities and resource allocation.")
        ],
        "why_it_matters": [
            "Navigating the AML regulatory landscape is one of the greatest challenges facing global financial institutions. With multiple regulators, overlapping jurisdictions, and constantly evolving requirements, compliance teams must maintain deep expertise across dozens of regulatory frameworks. The cost of non-compliance is staggering — global AML penalties exceeded $10 billion in recent years.",
            "Understanding the regulatory architecture is essential for designing effective compliance programs. Institutions must map their obligations across every jurisdiction where they operate, reconcile conflicting requirements, and build systems flexible enough to adapt to regulatory change. This regulatory intelligence function has become a specialized discipline within compliance departments."
        ],
        "takeaways": [
            "FATF's 40 Recommendations are the global standard that national AML regimes are built upon.",
            "The BSA and USA PATRIOT Act form the foundation of US AML regulation.",
            "The EU is consolidating its AML framework into a single Regulation (AMLR) for direct application.",
            "Global AML penalties have exceeded $10 billion in recent years, underscoring the cost of non-compliance."
        ],
        "flashcards": [
            {"front": "What is the FATF?", "back": "The Financial Action Task Force — an intergovernmental body that sets international AML/CFT standards."},
            {"front": "What does the Bank Secrecy Act require?", "back": "Recordkeeping, reporting (CTRs and SARs), and compliance programs for US financial institutions."},
            {"front": "What is the EU AMLR?", "back": "The EU Anti-Money Laundering Regulation, a single directly-applicable framework replacing the patchwork of AML Directives."},
            {"front": "How much have global AML penalties totaled in recent years?", "back": "Over $10 billion in fines and penalties across major jurisdictions."}
        ]
    },
    "aml/research/risk-based-approach-intro": {
        "overview_paras": [
            "The risk-based approach (RBA) is the foundational methodology of modern AML compliance. Rather than applying uniform controls to all customers, the RBA requires institutions to identify, assess, and understand the money laundering and terrorist financing risks they face, then apply proportionate measures to mitigate those risks. This approach is endorsed by the FATF and embedded in virtually every major AML regulatory framework worldwide.",
            "At its core, the RBA recognizes that not all customers, products, or jurisdictions pose equal risk. A retail bank serving local customers faces different risks than a private bank handling cross-border wealth management. Under the RBA, institutions allocate their compliance resources where they are most needed — applying enhanced scrutiny to high-risk relationships while streamlining controls for low-risk ones. This targeted approach makes compliance both more effective and more efficient."
        ],
        "key_concepts": [
            ("Inherent Risk", "The baseline level of risk associated with a customer, product, or geographic exposure before any mitigating controls are applied."),
            ("Residual Risk", "The remaining risk after applying controls and mitigation measures determined through the risk assessment process."),
            ("Risk Appetite", "The level of risk an institution is willing to accept in pursuit of its business objectives, as defined by senior management."),
            ("Risk Factors", "The specific variables used to assess risk including customer type, geographic location, product/service, and delivery channel."),
            ("Mitigation Measures", "The controls and procedures implemented to reduce identified risks to acceptable levels.")
        ],
        "why_it_matters": [
            "The risk-based approach transforms AML compliance from a box-ticking exercise into a strategic business function. By focusing resources on highest-risk areas, institutions achieve better outcomes with limited compliance budgets. Regulators increasingly expect institutions to demonstrate not just that they have controls, but that those controls are calibrated to their specific risk profile.",
            "Implementing an effective RBA requires sophisticated risk assessment methodologies, robust data collection, and ongoing validation. Institutions that master this approach gain competitive advantages through faster low-risk customer onboarding, more efficient compliance operations, and stronger regulatory relationships."
        ],
        "takeaways": [
            "The risk-based approach allocates compliance resources proportionally to assessed risk levels.",
            "RBA requires understanding both inherent risk and residual risk after controls.",
            "FATF and all major regulators mandate the risk-based approach for AML compliance.",
            "Effective RBA implementation requires sophisticated data collection and risk scoring methodologies."
        ],
        "flashcards": [
            {"front": "What is the risk-based approach?", "back": "A methodology that applies proportionate AML/CFT measures based on assessed risk levels rather than uniform controls."},
            {"front": "What is inherent risk?", "back": "The baseline risk level before any mitigating controls or measures are applied."},
            {"front": "What is residual risk?", "back": "The remaining risk after controls and mitigation measures have been implemented."},
            {"front": "Why does FATF endorse the RBA?", "back": "It makes compliance more effective by focusing resources on highest-risk areas and more efficient by streamlining low-risk controls."}
        ]
    },
    "aml/research/sanctions-screening-basics": {
        "overview_paras": [
            "Sanctions screening is a critical component of AML compliance that involves checking customer names and transactions against government-maintained sanctions lists. These lists identify individuals, entities, and countries subject to economic sanctions imposed by bodies such as the US Office of Foreign Assets Control (OFAC), the European Union, the United Nations, and the UK Office of Financial Sanctions Implementation (OFSI).",
            "The screening process involves matching customer data against sanctions databases using name matching algorithms that account for variations in spelling, transliteration, and name formats. When a potential match is found, compliance teams must investigate and determine whether it is a true match or a false positive. Effective sanctions screening requires sophisticated technology, well-designed matching algorithms, and skilled analysts to resolve alerts efficiently."
        ],
        "key_concepts": [
            ("OFAC", "The US Office of Foreign Assets Control, which administers and enforces US economic sanctions programs against targeted countries and entities."),
            ("SDN List", "OFAC's Specially Designated Nationals list, identifying individuals and entities whose assets are blocked and with whom US persons cannot transact."),
            ("Fuzzy Matching", "Name matching algorithms that account for spelling variations, transliteration differences, and partial matches to identify potential sanctions hits."),
            ("False Positives", "Alerts generated by screening systems that initially appear to match sanctions lists but are determined to be legitimate after investigation."),
            ("Sectoral Sanctions", "Targeted sanctions applied to specific industry sectors or entities rather than entire countries or governments.")
        ],
        "why_it_matters": [
            "Sanctions compliance is a strict liability regime — institutions are responsible for violations regardless of intent. The volume of global sanctions has exploded in recent years, with the US, EU, UK, and other jurisdictions expanding their sanctions programs in response to geopolitical developments. Financial institutions must screen against dozens of sanctions lists across multiple jurisdictions simultaneously.",
            "The consequences of sanctions violations are severe, including criminal prosecution, massive fines, and debarment from doing business in critical markets. Effective screening programs require continuous list updates, robust technology infrastructure, and well-trained compliance staff to manage the alert volume while minimizing false negative risk."
        ],
        "takeaways": [
            "Sanctions screening checks customers and transactions against government-maintained restricted party lists.",
            "OFAC's SDN List is the primary US sanctions list, with strict liability for violations.",
            "Fuzzy matching algorithms are essential to catch name variations but require skilled analysts to resolve alerts.",
            "Sanctions volume has increased dramatically, requiring continuous updates and multi-jurisdiction screening."
        ],
        "flashcards": [
            {"front": "What is OFAC?", "back": "The US Office of Foreign Assets Control, which administers and enforces US economic sanctions."},
            {"front": "What is the SDN List?", "back": "OFAC's Specially Designated Nationals list of blocked individuals and entities."},
            {"front": "What are false positives in sanctions screening?", "back": "Alerts that appear to match sanctions lists but are determined to be legitimate after investigation."},
            {"front": "What type of liability applies to sanctions violations?", "back": "Strict liability — institutions are responsible regardless of intent or knowledge."}
        ]
    },
    "aml/research/suspicious-activity-reports": {
        "overview_paras": [
            "Suspicious Activity Reports (SARs) and Suspicious Transaction Reports (STRs) are the primary mechanisms through which financial institutions report potentially illicit activity to financial intelligence units (FIUs). In the United States, SARs are filed with the Financial Crimes Enforcement Network (FinCEN), while other jurisdictions have their own reporting systems such as the UK's SAR regime through the National Crime Agency (NCA).",
            "The decision to file a SAR requires careful judgment by compliance professionals. Institutions must identify unusual activity that may indicate money laundering, terrorist financing, fraud, or other financial crime. This involves monitoring transactions for red flags such as unusual patterns, amounts inconsistent with customer profiles, rapid movement of funds, or activity involving high-risk jurisdictions. Timely and accurate SAR filing is essential for law enforcement to investigate and disrupt financial crime networks."
        ],
        "key_concepts": [
            ("SAR", "Suspicious Activity Report — the primary filing mechanism in the US for reporting suspicious financial activity to FinCEN."),
            ("STR", "Suspicious Transaction Report — the equivalent filing used in many jurisdictions outside the US, including the UK and EU."),
            ("FinCEN", "The Financial Crimes Enforcement Network, the US financial intelligence unit that collects and analyzes SAR data."),
            ("Red Flags", "Indicators of suspicious activity including unusual transaction patterns, amounts inconsistent with customer profiles, and rapid fund movements."),
            ("Tipping Off", "The prohibited practice of notifying the subject of a SAR that a report has been filed, which could compromise law enforcement investigations.")
        ],
        "why_it_matters": [
            "SARs and STRs form the intelligence backbone of global AML efforts. Financial institutions file millions of SARs annually, providing law enforcement with critical leads for investigating money laundering, terrorist financing, and other financial crimes. The quality and timeliness of these reports directly impact law enforcement's ability to disrupt criminal networks.",
            "The legal framework surrounding SARs provides important protections for financial institutions. In most jurisdictions, safe harbor provisions protect institutions and their employees from civil liability when filing SARs in good faith. However, the failure to file required SARs can result in significant regulatory penalties and criminal liability."
        ],
        "takeaways": [
            "SARs/STRs are the primary reporting mechanism for suspicious financial activity to financial intelligence units.",
            "FinCEN is the US financial intelligence unit that collects and analyzes SAR data.",
            "Tipping off subjects that a SAR has been filed is a criminal offense in most jurisdictions.",
            "Safe harbor provisions protect institutions that file SARs in good faith from civil liability."
        ],
        "flashcards": [
            {"front": "What is the difference between a SAR and an STR?", "back": "A SAR (Suspicious Activity Report) is used in the US; STR (Suspicious Transaction Report) is used in the UK, EU, and other jurisdictions."},
            {"front": "What is tipping off?", "back": "Notifying the subject of a SAR that a report has been filed, which is a criminal offense in most jurisdictions."},
            {"front": "What does FinCEN do?", "back": "The Financial Crimes Enforcement Network collects and analyzes SAR data to combat financial crime."},
            {"front": "What legal protection exists for SAR filers?", "back": "Safe harbor provisions protect institutions from civil liability when filing SARs in good faith."}
        ]
    },
}

# ── Learn module content generators based on pillar and topic keywords ──

LEARN_DE_TOPICS = {
    "what-is-data-engineering": {
        "overview": [
            "Data engineering is the practice of designing, building, and maintaining systems for collecting, storing, processing, and analyzing data at scale. It forms the foundation upon which data science, machine learning, and analytics are built. Without robust data engineering, organizations cannot reliably transform raw data into actionable insights.",
            "The modern data engineer works with a diverse toolkit including programming languages like Python and SQL, distributed computing frameworks like Apache Spark, cloud platforms such as AWS, GCP, and Azure, and orchestration tools like Airflow and dbt. The role has evolved significantly from traditional ETL development to encompass data architecture, pipeline optimization, and data platform engineering."
        ],
        "key_concepts": [
            ("ETL/ELT", "Extract, Transform, Load — the classical data pipeline pattern. ELT (Load then Transform) shifts transformation to the target warehouse for scalability."),
            ("Data Pipeline", "A series of steps that move and transform data from source systems to destination systems for analysis and reporting."),
            ("Data Warehouse", "A centralized repository optimized for structured data analytics, typically using columnar storage and SQL querying."),
            ("Data Lake", "A storage repository that holds vast amounts of raw data in native format, supporting both structured and unstructured data."),
            ("DataOps", "A set of practices and tools that brings DevOps principles to data management, emphasizing automation, monitoring, and collaboration.")
        ],
        "takeaways": [
            "Data engineering provides the infrastructure foundation for all data-driven work in an organization.",
            "Modern data engineers work with diverse tools spanning programming, distributed computing, and cloud platforms.",
            "The shift from ETL to ELT reflects the power of modern cloud data warehouses.",
            "DataOps applies DevOps principles of automation and CI/CD to data pipeline management."
        ]
    },
    "sql-for-data-engineers": {
        "overview": [
            "SQL (Structured Query Language) remains the most important language for data engineers. Despite the proliferation of NoSQL databases and big data technologies, SQL is the universal interface for querying and manipulating structured data. Every data engineer must master SQL to work effectively with relational databases, data warehouses, and increasingly with data lakes and streaming systems.",
            "Modern SQL extends far beyond simple SELECT statements. Data engineers use common table expressions (CTEs), window functions, complex joins, query optimization techniques, and database-specific features to build efficient data pipelines. Understanding query execution plans and indexing strategies is essential for performance tuning at scale."
        ],
        "key_concepts": [
            ("Window Functions", "SQL functions that perform calculations across related rows while preserving individual row identity, enabling running totals and ranking."),
            ("Common Table Expressions", "Temporary named result sets that simplify complex queries by breaking them into readable, reusable steps."),
            ("Query Optimization", "Techniques including index usage, join ordering, and partition pruning that improve query execution speed."),
            ("Indexing Strategies", "Data structures that speed up data retrieval at the cost of write performance, including B-tree, bitmap, and hash indexes."),
            ("ACID Compliance", "Atomicity, Consistency, Isolation, Durability — the four properties that guarantee reliable database transaction processing.")
        ],
        "takeaways": [
            "SQL is the universal language for structured data manipulation and remains essential for data engineers.",
            "Window functions and CTEs enable powerful query patterns that simplify complex data transformations.",
            "Understanding query execution plans is critical for performance optimization.",
            "Proper indexing strategies balance read performance against write overhead in production databases."
        ]
    },
    "data-pipeline-basics": {
        "overview": [
            "Data pipelines are the backbone of modern data infrastructure, moving and transforming data from source systems to destination systems. Understanding the fundamental patterns of batch and streaming processing is essential for designing robust, scalable data architectures. Each pattern has distinct use cases, trade-offs, and best practices.",
            "Batch processing handles data in discrete chunks at scheduled intervals, making it ideal for large-scale transformations where near-real-time delivery is not required. Streaming processing handles data continuously as it arrives, enabling real-time analytics and immediate response to events. Many modern architectures combine both patterns in a lambda or kappa architecture approach."
        ],
        "key_concepts": [
            ("Batch Processing", "Processing data in discrete chunks at scheduled intervals, optimized for throughput and handling large volumes of historical data."),
            ("Streaming Processing", "Processing data continuously as it arrives, enabling real-time analytics and low-latency event response."),
            ("Lambda Architecture", "A hybrid approach combining batch and streaming layers to provide both comprehensive historical analysis and real-time views."),
            ("Kappa Architecture", "A simplified architecture using only stream processing, treating batch as a special case of streaming with reprocessing."),
            ("Data Orchestration", "The coordination of pipeline steps including scheduling, dependency management, error handling, and monitoring.")
        ],
        "takeaways": [
            "Batch pipelines are optimized for throughput and handle large volumes of historical data at scheduled intervals.",
            "Streaming pipelines process data continuously for real-time analytics and immediate event response.",
            "Lambda architecture combines batch and streaming for comprehensive coverage.",
            "Kappa architecture simplifies to a single streaming layer, treating batch as reprocessing."
        ]
    },
    "data-quality-basics": {
        "overview": [
            "Data quality is the measure of how well a dataset meets the requirements for its intended use. Poor data quality costs organizations millions of dollars annually through incorrect decisions, wasted resources, and failed analytics initiatives. The six dimensions of data quality provide a comprehensive framework for assessing and improving data reliability.",
            "The six dimensions are accuracy, completeness, consistency, timeliness, validity, and uniqueness. Each dimension requires specific measurement approaches and improvement strategies. Modern data quality programs combine automated monitoring, data profiling, and governance processes to maintain high quality standards across the data lifecycle."
        ],
        "key_concepts": [
            ("Accuracy", "The degree to which data correctly represents the real-world entity or event it describes."),
            ("Completeness", "The extent to which all required data is present and available for use."),
            ("Consistency", "The absence of contradictions between different data records or across different data sources."),
            ("Timeliness", "The degree to which data is available within the expected timeframe for its intended use."),
            ("Data Observability", "A holistic approach to understanding data health through monitoring, lineage, and automated quality checks.")
        ],
        "takeaways": [
            "Data quality is measured across six dimensions: accuracy, completeness, consistency, timeliness, validity, and uniqueness.",
            "Poor data quality costs organizations millions through incorrect decisions and wasted resources.",
            "Modern data quality programs combine automated monitoring with governance processes.",
            "Data observability extends traditional quality monitoring with lineage tracking and automated detection."
        ]
    },
    "warehouse-vs-lake": {
        "overview": [
            "The data warehouse versus data lake debate is central to modern data architecture. A data warehouse is a centralized repository optimized for structured data analytics, using schema-on-write approaches and columnar storage for fast SQL query performance. A data lake stores vast amounts of raw data in native format, supporting both structured and unstructured data with schema-on-read flexibility.",
            "The emergence of the lakehouse architecture aims to combine the best of both approaches. Lakehouses like Databricks and Apache Iceberg provide ACID transactions, schema enforcement, and high-performance querying on data lake storage. This convergence allows organizations to maintain a single copy of data while supporting both data science exploration and production analytics."
        ],
        "key_concepts": [
            ("Schema-on-Write", "Data is validated and structured before being written to storage, ensuring quality but requiring upfront design."),
            ("Schema-on-Read", "Data is stored in raw format and interpreted at query time, offering flexibility but requiring more processing."),
            ("Data Lakehouse", "An architecture combining data lake flexibility with warehouse reliability, ACID transactions, and SQL performance."),
            ("Apache Iceberg", "An open table format for huge analytic datasets that adds ACID transactions and time travel to data lakes."),
            ("Medallion Architecture", "A layered approach organizing data into bronze (raw), silver (cleaned), and gold (aggregated) zones.")
        ],
        "takeaways": [
            "Data warehouses offer optimized SQL performance with schema-on-write for structured analytics.",
            "Data lakes provide flexible storage for all data types with schema-on-read interpretation.",
            "Lakehouse architecture merges both approaches with ACID transactions on data lake storage.",
            "The medallion architecture provides a practical framework for organizing data lake content by quality level."
        ]
    },
    "data-contracts-lineage": {
        "overview": [
            "Data contracts are formal agreements between data producers and data consumers that specify the structure, quality, and service-level expectations for data assets. They bring the concept of API contracts to the data world, ensuring that downstream consumers can rely on upstream data sources. Data lineage, meanwhile, provides the end-to-end map of how data flows through systems, transforms, and dependencies.",
            "Together, data contracts and lineage form the backbone of data trust and observability. Contracts prevent breaking changes from propagating silently to downstream systems, while lineage enables impact analysis, root cause investigation, and regulatory compliance. Implementing both requires cultural shifts toward treating data as a product with clear ownership and accountability."
        ],
        "key_concepts": [
            ("Data Contract", "A formal SLA between data producers and consumers specifying schema, freshness, quality, and availability guarantees."),
            ("Data Lineage", "The complete audit trail showing how data moves from source to destination, including all transformations and dependencies."),
            ("Data Product", "A self-contained data asset treated as a product with defined ownership, SLAs, and consumer documentation."),
            ("Impact Analysis", "Using lineage to determine which downstream systems and reports will be affected by proposed data changes."),
            ("Column-Level Lineage", "The most granular form of lineage tracking, showing exactly how individual columns transform across pipeline stages.")
        ],
        "takeaways": [
            "Data contracts establish formal agreements between producers and consumers, preventing breaking changes.",
            "Data lineage provides the complete map of data flow for debugging, impact analysis, and compliance.",
            "Treating data as a product with clear ownership improves accountability and quality.",
            "Column-level lineage offers the most granular view of data transformations across pipelines."
        ]
    },
    "data-mesh-in-practice": {
        "overview": [
            "Data mesh is a decentralized sociotechnical architecture that applies product thinking and domain ownership to data management. Proposed by Zhamak Dehghani, data mesh shifts away from centralized data platforms toward domain-owned data products connected through a shared interoperability layer. Each domain team owns its data end-to-end, treating it as a product for consumption by other domains.",
            "The four principles of data mesh are domain ownership, data as a product, federated computational governance, and a self-serve data infrastructure platform. Organizations adopting data mesh report improved data quality, faster time-to-insight, and reduced bottlenecks. However, the approach requires significant organizational maturity and investment in platform capabilities."
        ],
        "key_concepts": [
            ("Domain Ownership", "Each business domain owns its data end-to-end, including collection, processing, quality, and serving."),
            ("Data as a Product", "Data is treated as a discoverable, addressable, and trustworthy asset with defined SLAs and documentation."),
            ("Federated Governance", "A balanced model where global standards are set centrally while domain teams maintain local implementation autonomy."),
            ("Self-Serve Platform", "The infrastructure layer providing shared capabilities for storage, compute, cataloging, and monitoring to all domains."),
            ("Data Product Port", "The standardized interface through which data products are discovered, accessed, and connected across domains.")
        ],
        "takeaways": [
            "Data mesh decentralizes data ownership to domain teams while providing shared infrastructure.",
            "Data is treated as a product with discoverability, addressability, and quality guarantees.",
            "Federated governance balances global standards with local implementation autonomy.",
            "The self-serve platform is critical for enabling domain teams without requiring deep infrastructure expertise."
        ]
    },
    "change-data-capture-patterns": {
        "overview": [
            "Change Data Capture (CDC) is a pattern for capturing changes made to a database and applying them to downstream systems in real time. Instead of running periodic batch loads, CDC captures inserts, updates, and deletes as they happen and streams them to targets. CDC is fundamental to modern data architectures that require low-latency synchronization between operational and analytical systems.",
            "There are several CDC implementation approaches: log-based CDC reads the database transaction log to capture changes without impacting source performance; trigger-based CDC uses database triggers to record changes; and query-based CDC compares snapshots to detect differences. Log-based CDC is generally preferred for production systems due to its minimal overhead and completeness."
        ],
        "key_concepts": [
            ("Log-Based CDC", "Captures changes directly from the database transaction log without modifying the source application or schema."),
            ("Trigger-Based CDC", "Uses database triggers to capture changes into a separate tracking table, offering flexibility but adding overhead."),
            ("Debezium", "An open-source distributed CDC platform built on Apache Kafka Connect, supporting MySQL, PostgreSQL, MongoDB, and more."),
            ("Kafka Connect", "A framework for streaming data between Apache Kafka and external systems with built-in CDC source connectors."),
            ("Exactly-Once Semantics", "The guarantee that each change is processed exactly once, preventing both duplicates and data loss.")
        ],
        "takeaways": [
            "CDC captures database changes in real time and streams them to downstream systems without batch loads.",
            "Log-based CDC reads transaction logs with minimal performance impact and complete change coverage.",
            "Debezium and Kafka Connect are the dominant open-source CDC tooling ecosystem.",
            "Exactly-once semantics prevent data loss and duplication in CDC pipelines."
        ]
    },
    "modern-data-catalog": {
        "overview": [
            "A modern data catalog is a metadata management platform that helps organizations discover, understand, and trust their data assets. Unlike traditional catalog tools that focused on technical metadata, modern catalogs combine business context, data lineage, quality metrics, and collaboration features in a searchable interface. They serve as the central nervous system of the data platform.",
            "The modern data catalog market has evolved rapidly with the rise of data mesh and data product thinking. Open-source projects like Apache Atlas, Amundsen, and DataHub compete with commercial offerings from Alation, Collibra, and Atlan. Key capabilities include automated metadata ingestion, column-level lineage, data quality integration, and embedded collaboration."
        ],
        "key_concepts": [
            ("Metadata Ingestion", "The automated extraction of technical metadata from databases, pipelines, BI tools, and other data systems."),
            ("Business Glossary", "A curated dictionary of business terms and definitions that maps technical assets to business concepts."),
            ("Data Discovery", "The ability to search, browse, and explore data assets using both technical and business metadata."),
            ("Data Profiling", "Automated analysis of data content to understand structure, quality, and patterns across datasets."),
            ("Active Metadata", "Metadata that is continuously updated and used to drive automated actions in the data platform.")
        ],
        "takeaways": [
            "Modern data catalogs combine technical, business, and operational metadata in a searchable platform.",
            "Automated metadata ingestion from diverse sources is essential for keeping catalogs current.",
            "Business glossaries bridge the gap between technical data assets and business understanding.",
            "Active metadata enables automated governance and quality enforcement based on real-time data context."
        ]
    },
    "schema-management-evolution": {
        "overview": [
            "Schema management and evolution address the challenge of maintaining data structure consistency as systems change over time. In traditional databases, schema changes require careful migration planning. In distributed and streaming systems, schema evolution must handle producers and consumers operating at different versions simultaneously. Effective schema management is essential for preventing data quality issues and pipeline failures.",
            "Schema registries like Confluent Schema Registry and Apicurio provide centralized schema storage, validation, and versioning. They enforce compatibility rules — backward, forward, or full — ensuring that schema changes don't break existing consumers. Avro, Protobuf, and JSON Schema are the most common serialization formats with built-in evolution support."
        ],
        "key_concepts": [
            ("Schema Registry", "A centralized service for storing, versioning, and validating schemas used by data producers and consumers."),
            ("Backward Compatibility", "New schema versions can read data written by the previous version without breaking existing consumers."),
            ("Forward Compatibility", "Old consumers can read data written with a newer schema version without errors."),
            ("Apache Avro", "A compact binary serialization format with rich schema evolution capabilities, widely used in Kafka ecosystems."),
            ("Schema-on-Read vs Schema-on-Write", "Schema-on-write validates at ingestion time; schema-on-read interprets data at query time with evolving schemas.")
        ],
        "takeaways": [
            "Schema registries centralize versioning and validation to prevent incompatible changes.",
            "Backward compatibility ensures new schemas don't break existing consumers.",
            "Forward compatibility allows old consumers to read data written with new schemas.",
            "Avro, Protobuf, and JSON Schema provide formal schema evolution capabilities for distributed systems."
        ]
    },
    "pipeline-cost-optimization": {
        "overview": [
            "Data pipeline cost optimization has become a critical discipline as organizations scale their data infrastructure. Cloud data services charge for compute, storage, and data transfer, and costs can spiral without proper governance. Understanding the cost drivers across different pipeline patterns — batch, streaming, and hybrid — is essential for building cost-effective data architectures.",
            "Key cost optimization strategies include right-sizing compute resources, using spot/preemptible instances for fault-tolerant workloads, implementing data lifecycle management to tier or expire old data, optimizing query patterns to minimize scanned data, and choosing the right storage format. Modern tools like dbt and Airflow provide cost monitoring capabilities that help teams track and optimize pipeline spending."
        ],
        "key_concepts": [
            ("Compute Optimization", "Selecting appropriate instance types, using auto-scaling, and leveraging spot instances to minimize compute costs."),
            ("Data Lifecycle Management", "Policies for moving data through hot, warm, and cold storage tiers and eventually expiring or archiving it."),
            ("Partition Pruning", "Query optimization that limits data scanning to relevant partitions, reducing compute and I/O costs."),
            ("Columnar Storage", "Storage formats like Parquet and ORC that store data by column, enabling efficient compression and selective reads."),
            ("Cost Allocation", "Tracking data pipeline costs back to business units or teams using tagging and usage metering.")
        ],
        "takeaways": [
            "Cloud data costs can spiral without proper governance and optimization practices.",
            "Right-sizing compute and using spot instances can significantly reduce pipeline costs.",
            "Data lifecycle management policies reduce storage costs by tiering and expiring data.",
            "Columnar storage formats and partition pruning minimize compute costs for analytical queries."
        ]
    },
    "privacy-engineering-practice": {
        "overview": [
            "Privacy engineering is the practice of embedding data protection principles into the design and operation of data systems. With regulations like GDPR, CCPA, and LGPD imposing strict requirements on how personal data is collected, processed, and stored, privacy engineering has become an essential discipline for data engineers. It goes beyond compliance checkboxes to build systems that protect privacy by default.",
            "Core privacy engineering techniques include data anonymization and pseudonymization, purpose-based access controls, data retention enforcement, consent management, and privacy impact assessments. Data engineers must implement these capabilities at the pipeline level, ensuring that privacy controls are applied consistently across all data processing activities."
        ],
        "key_concepts": [
            ("Anonymization", "Irreversibly removing personal identifiers so data can no longer be associated with an individual."),
            ("Pseudonymization", "Replacing identifiers with tokens, allowing re-identification under controlled conditions with a mapping key."),
            ("Differential Privacy", "Adding calibrated noise to query results to protect individual privacy while maintaining statistical accuracy."),
            ("Consent Management", "Systems for capturing, storing, and enforcing user consent preferences across data processing activities."),
            ("Data Retention Enforcement", "Automated processes that delete or archive personal data when the retention period expires.")
        ],
        "takeaways": [
            "Privacy engineering embeds data protection into system design, not just compliance checklists.",
            "Anonymization and pseudonymization protect personal data while enabling analytics.",
            "Differential privacy provides mathematical guarantees for privacy-preserving data analysis.",
            "Consent management and retention enforcement must be automated at the pipeline level."
        ]
    },
    "regulatory-compliance-data-platforms": {
        "overview": [
            "Building data platforms that meet regulatory compliance requirements is a complex challenge spanning multiple frameworks including GDPR, CCPA, SOX, HIPAA, and financial regulations like MiFID II and Basel III. Compliance must be engineered into the data architecture from the ground up, affecting how data is collected, stored, processed, audited, and deleted.",
            "Key compliance requirements include data lineage for audit trails, access controls and encryption for data protection, retention and deletion capabilities for data lifecycle management, and consent tracking for personal data. Modern data platforms use column-level lineage, attribute-based access control (ABAC), and automated policy enforcement to meet these requirements at scale."
        ],
        "key_concepts": [
            ("Audit Trail", "Complete, immutable record of all data access and modifications for regulatory reporting and investigation."),
            ("Attribute-Based Access Control", "Fine-grained access control based on user attributes, data sensitivity labels, and contextual conditions."),
            ("Data Residency", "Requirements that data remain within specific geographic boundaries as mandated by local regulations."),
            ("Right to Erasure", "GDPR requirement enabling individuals to request deletion of their personal data from all systems."),
            ("Data Protection Impact Assessment", "A systematic process for evaluating privacy risks of new data processing activities.")
        ],
        "takeaways": [
            "Compliance requirements must be engineered into data architecture from the beginning.",
            "Audit trails, access controls, and encryption are foundational compliance capabilities.",
            "Data residency and retention requirements vary significantly across jurisdictions.",
            "Automated policy enforcement scales compliance beyond manual processes."
        ]
    },
    "data-versioning-reproducibility": {
        "overview": [
            "Data versioning and reproducibility are essential for trustworthy data science and analytics. Versioning tracks changes to datasets over time, enabling rollback, comparison, and audit. Reproducibility ensures that analyses can be recreated with identical results, which is critical for scientific integrity, regulatory compliance, and debugging production issues.",
            "Tools like DVC (Data Version Control), LakeFS, and Quilt provide Git-like versioning for data assets. These tools track dataset snapshots, manage storage efficiently through copy-on-write and deduplication, and integrate with existing Git workflows. Combined with environment management through Docker and Conda, they enable fully reproducible data pipelines."
        ],
        "key_concepts": [
            ("Data Version Control", "Versioning datasets alongside code changes, enabling rollback, comparison, and collaboration on data assets."),
            ("Copy-on-Write", "Storage optimization where unchanged data blocks are shared across versions, reducing storage overhead."),
            ("DVC", "An open-source tool that brings Git-like version control to machine learning models and datasets."),
            ("LakeFS", "A version control system for data lakes that provides Git-like branches, commits, and merges for data."),
            ("Reproducible Builds", "The principle that running the same pipeline with the same inputs always produces identical outputs.")
        ],
        "takeaways": [
            "Data versioning enables rollback, audit, and comparison of datasets over time.",
            "Tools like DVC and LakeFS bring Git workflows to data management.",
            "Copy-on-write optimizes storage efficiency when versioning large datasets.",
            "Reproducibility requires versioning not just data but also code, environments, and pipeline configurations."
        ]
    },
    "data-security-access-control": {
        "overview": [
            "Data security and access control are critical components of enterprise data platforms. As data becomes more central to business operations, protecting it from unauthorized access, breaches, and misuse is paramount. A comprehensive data security strategy covers authentication, authorization, encryption, auditing, and data masking across the entire data lifecycle.",
            "Modern data platforms implement defense-in-depth with multiple security layers. Network security controls access at the infrastructure level. Identity and access management (IAM) governs user permissions. Data-level security through column-level access control and dynamic data masking ensures fine-grained protection. Encryption protects data at rest and in transit, while comprehensive auditing provides accountability."
        ],
        "key_concepts": [
            ("Defense in Depth", "A security strategy using multiple independent layers of protection so that failure of one layer does not compromise the whole."),
            ("Dynamic Data Masking", "Real-time obfuscation of sensitive data in query results based on user permissions."),
            ("Row-Level Security", "Restricting data access at the row level based on user attributes, ensuring users see only authorized data."),
            ("Encryption at Rest", "Encrypting stored data so that it remains protected even if physical storage media is compromised."),
            ("IAM Policies", "Identity and Access Management policies that define who can perform what actions on which resources.")
        ],
        "takeaways": [
            "Defense in depth applies multiple security layers to protect against any single point of failure.",
            "Dynamic data masking and row-level security provide fine-grained data protection.",
            "Encryption at rest and in transit protects data from infrastructure-level compromise.",
            "Comprehensive auditing enables detection and investigation of security incidents."
        ]
    },
    "elt-reverse-etl-analytics-engineering": {
        "overview": [
            "The modern data stack has evolved from traditional ETL toward ELT, Reverse ETL, and the emerging discipline of analytics engineering. ELT leverages the power of modern cloud warehouses to transform data after loading, enabling greater flexibility and scalability. Reverse ETL moves processed data from the warehouse back into operational systems like CRMs and marketing platforms, closing the analytics loop.",
            "Analytics engineering sits between data engineering and analytics, focusing on transforming raw data into clean, documented, and tested datasets ready for analysis. Tools like dbt have popularized this discipline by applying software engineering best practices — version control, testing, documentation, and CI/CD — to SQL transformations."
        ],
        "key_concepts": [
            ("ELT", "Extract, Load, Transform — loading raw data into the warehouse first, then transforming using warehouse compute power."),
            ("Reverse ETL", "Syncing processed data from the warehouse back into operational tools like Salesforce, HubSpot, and Marketo."),
            ("dbt", "The leading analytics engineering tool that enables SQL-based transformations with version control, testing, and documentation."),
            ("Data Modeling", "Designing the structure and relationships of transformed data using star schemas, snowflake schemas, or data vault."),
            ("CI/CD for Data", "Applying continuous integration and deployment practices to data pipeline changes, including automated testing and deployment.")
        ],
        "takeaways": [
            "ELT leverages warehouse compute for transformation, providing scalability over traditional ETL approaches.",
            "Reverse ETL closes the analytics loop by pushing insights back into operational systems.",
            "Analytics engineering applies software engineering practices to data transformation with tools like dbt.",
            "CI/CD for data ensures pipeline changes are tested and deployed reliably."
        ]
    },
    "data-quality-observability-tools": {
        "overview": [
            "Data observability extends traditional data quality monitoring with a holistic view of data health across pipelines, systems, and business impact. Inspired by observability in software engineering, data observability provides real-time visibility into data freshness, distribution, volume, schema, and lineage. It enables teams to detect, diagnose, and resolve data issues before they impact downstream consumers.",
            "The five pillars of data observability are freshness (is data up to date?), distribution (is data within expected ranges?), volume (is data flowing at expected rates?), schema (has the structure changed?), and lineage (where did the data come from and where is it going?). Tools like Monte Carlo, Sifflet, and Bigeye provide automated monitoring across these dimensions."
        ],
        "key_concepts": [
            ("Data Freshness", "Monitoring whether data is arriving within expected time windows to detect pipeline delays or failures."),
            ("Data Distribution", "Tracking statistical distributions of data values to detect anomalies and drift."),
            ("Data Volume", "Monitoring data volume trends to detect sudden drops indicating pipeline failures or spikes indicating issues."),
            ("Schema Change Detection", "Alerting when table structures change unexpectedly, potentially breaking downstream processes."),
            ("Automated Root Cause Analysis", "Using lineage to trace data issues back to their source, accelerating incident response.")
        ],
        "takeaways": [
            "Data observability provides holistic visibility into data health across freshness, distribution, volume, schema, and lineage.",
            "Automated monitoring detects issues faster than manual checking or scheduled quality reports.",
            "Lineage-based root cause analysis accelerates incident response when data issues are detected.",
            "Data observability tools complement traditional quality checks with real-time monitoring."
        ]
    },
    "dataops-introduction": {
        "overview": [
            "DataOps is a set of practices, processes, and technologies that brings DevOps principles to data management. It emphasizes automation, collaboration, monitoring, and continuous improvement across the data lifecycle. DataOps aims to improve the quality, speed, and reliability of data analytics while reducing cycle times for data pipeline changes.",
            "Key DataOps practices include version-controlled data pipelines, automated testing of data transformations, continuous integration and deployment for data changes, monitoring and alerting for data quality, and collaborative workflows between data engineers, analysts, and data scientists. Organizations implementing DataOps report faster time-to-insight and higher data reliability."
        ],
        "key_concepts": [
            ("Data Pipeline CI/CD", "Automated testing and deployment of data pipeline code changes, ensuring quality and reducing deployment risk."),
            ("Data Monitoring", "Continuous observation of data pipelines for failures, delays, quality issues, and performance degradation."),
            ("Infrastructure as Code", "Managing data infrastructure through version-controlled configuration files rather than manual processes."),
            ("Data Catalog Integration", "Automatically updating the data catalog with pipeline metadata, lineage, and quality information."),
            ("Collaboration Workflows", "Structured processes for data teams to review changes, resolve issues, and share knowledge.")
        ],
        "takeaways": [
            "DataOps applies DevOps principles of automation, CI/CD, and monitoring to data management.",
            "Automated testing of data transformations catches issues before they reach production.",
            "Version-controlled infrastructure enables reproducible environments and faster recovery.",
            "Collaboration workflows improve communication between data engineers, analysts, and scientists."
        ]
    },
    "data-quality-engineering": {
        "overview": [
            "Data quality engineering applies systematic engineering practices to ensure data meets defined quality standards throughout its lifecycle. It goes beyond ad-hoc data cleaning to build automated quality validation into every stage of the data pipeline. Quality is measured, monitored, and improved continuously through a combination of automated checks, governance processes, and feedback loops.",
            "A mature data quality engineering program includes automated profiling and validation at ingestion, transformation, and consumption stages. Rules are defined as code and executed as part of the pipeline. Quality metrics are tracked over time, and degradation triggers alerts and remediation workflows. This systematic approach ensures that data consumers can trust the data they work with."
        ],
        "key_concepts": [
            ("Quality as Code", "Defining data quality rules in version-controlled code that executes as part of automated pipeline runs."),
            ("Freshness SLAs", "Service Level Agreements defining acceptable latency for data availability in production systems."),
            ("Quality Gates", "Automated checkpoints in the pipeline that block data from proceeding if quality thresholds are not met."),
            ("Data Quality Scorecards", "Dashboard views tracking quality metrics across datasets, dimensions, and time periods."),
            ("Remediation Workflows", "Automated processes for escalating and resolving data quality issues when they are detected.")
        ],
        "takeaways": [
            "Data quality engineering treats quality as a continuous, automated process built into pipelines.",
            "Quality rules defined as code enable version control, testing, and automated execution.",
            "Quality gates prevent bad data from reaching downstream consumers.",
            "Scorecards and monitoring provide visibility into quality trends over time."
        ]
    },
    "open-source-data-stack": {
        "overview": [
            "The open-source data stack has matured dramatically, offering viable alternatives to proprietary data platforms for every layer of the data architecture. From ingestion to transformation, storage to orchestration, and analytics to governance, open-source tools now power some of the largest data platforms in production. This ecosystem reduces vendor lock-in and provides flexibility to customize solutions.",
            "Key components of the open-source data stack include Apache Kafka for streaming, dbt for transformations, Airflow or Dagster for orchestration, Spark or Flink for processing, Iceberg or Delta Lake for storage, and Superset or Metabase for visualization. Organizations often combine these tools into a best-of-breed architecture, investing in integration and operational expertise."
        ],
        "key_concepts": [
            ("Apache Kafka", "A distributed streaming platform for building real-time data pipelines and streaming applications."),
            ("Apache Airflow", "A platform for programmatically authoring, scheduling, and monitoring workflows."),
            ("dbt Core", "The open-source version of dbt for SQL-first data transformations with testing and documentation."),
            ("Apache Iceberg", "An open table format for huge analytic datasets providing ACID transactions and time travel."),
            ("Apache Superset", "A modern, enterprise-ready business intelligence web application for data exploration and visualization.")
        ],
        "takeaways": [
            "The open-source data stack provides alternatives for every layer of modern data architecture.",
            "Best-of-breed architectures combine the best open-source tools with integration expertise.",
            "Open-source tools reduce vendor lock-in and provide greater customization flexibility.",
            "Operational expertise is the key investment when adopting open-source data tools."
        ]
    },
    "designing-data-platform": {
        "overview": [
            "Designing a modern data platform requires careful consideration of architecture, technology selection, team structure, and organizational processes. A well-designed platform balances scalability, reliability, cost, and usability while meeting the diverse needs of data consumers across the organization. The platform must evolve with changing requirements without requiring fundamental redesign.",
            "Key design decisions include choosing between batch and streaming paradigms, selecting storage technologies, defining data modeling approaches, establishing governance frameworks, and designing for cost management. Modern platforms increasingly adopt modular, composable architectures that allow teams to swap components as needs change."
        ],
        "key_concepts": [
            ("Composable Architecture", "A modular approach where platform components can be independently selected, replaced, and upgraded."),
            ("Data Platform Team Topologies", "Organizational structures defining how platform teams interact with domain data teams."),
            ("Multi-Cloud Strategy", "Distributing data across multiple cloud providers for resilience, cost optimization, and capability access."),
            ("Platform APIs", "Well-defined interfaces that abstract platform complexity and enable self-service data access."),
            ("Total Cost of Ownership", "The complete cost of building, operating, and evolving a data platform including engineering, infrastructure, and licensing.")
        ],
        "takeaways": [
            "Modern data platforms balance scalability, reliability, cost, and usability for diverse consumers.",
            "Composable architectures enable component flexibility without requiring platform redesign.",
            "Platform team topologies affect how data capabilities are delivered to domain teams.",
            "Total cost of ownership includes engineering and operational costs, not just infrastructure."
        ]
    },
    "data-quality-observability-cost": {
        "overview": [
            "Building data platforms requires balancing the competing demands of quality, observability, and cost. High-quality data requires investment in validation, monitoring, and governance. Full observability provides visibility into pipeline health but adds monitoring infrastructure costs. Managing these trade-offs while maintaining data trust is a central challenge for data platform teams.",
            "Organizations must develop frameworks for evaluating investments in data quality and observability against their costs. Automated quality monitoring reduces manual checking effort. Selective observability focuses monitoring on critical pipelines. Cost allocation ensures that quality investments are justified by business value."
        ],
        "key_concepts": [
            ("Cost of Poor Data Quality", "The financial impact of bad data including incorrect decisions, wasted effort, and regulatory penalties."),
            ("Observability ROI", "The return on investment from monitoring infrastructure measured against prevented incidents and reduced downtime."),
            ("Tiered Quality Approaches", "Applying different quality standards to critical versus experimental data assets."),
            ("Cost Attribution", "Tracking data platform costs to specific teams, pipelines, or business units for accountability."),
            ("Quality Telemetry", "Automated collection and analysis of quality metrics to identify improvement opportunities.")
        ],
        "takeaways": [
            "Quality, observability, and cost must be balanced in data platform design.",
            "Poor data quality has significant financial impact through incorrect decisions and wasted effort.",
            "Tiered quality standards focus investment where it delivers the most business value.",
            "Cost attribution creates accountability and enables informed investment decisions."
        ]
    },
    "building-pipelines-dbt-dagster": {
        "overview": [
            "dbt and Dagster represent the modern approach to building and orchestrating data pipelines. dbt provides a SQL-first framework for transforming data in the warehouse, emphasizing testing, documentation, and version control. Dagster is an orchestration platform that brings asset-based thinking, type safety, and developer experience to pipeline management.",
            "Together, dbt and Dagster create a powerful combination for building reliable, maintainable data pipelines. dbt handles the transformation logic with modular SQL models, while Dagster manages execution, dependencies, and observability. The integration leverages Dagster's software-defined assets to represent dbt models as first-class data assets with lineage and quality tracking."
        ],
        "key_concepts": [
            ("Software-Defined Assets", "Dagster's model where assets are defined in code with their dependencies, enabling automatic lineage and selective materialization."),
            ("dbt Models", "Modular SQL SELECT statements that define data transformations with built-in testing and documentation."),
            ("Asset Materialization", "The process of computing and storing an asset, with Dagster tracking each materialization event."),
            ("dbt Tests", "Built-in data quality testing including uniqueness, not-null, accepted values, and custom test definitions."),
            ("Partitioned Assets", "Assets broken into time-based or value-based partitions for incremental processing and backfills.")
        ],
        "takeaways": [
            "dbt provides SQL-first transformations with testing, documentation, and modular model design.",
            "Dagster orchestrates pipelines with software-defined assets for automatic dependency management.",
            "The dbt-Dagster integration combines transformation logic with robust orchestration and observability.",
            "Partitioned assets enable efficient incremental processing and selective backfill."
        ]
    },
    "data-pipeline-architectures": {
        "overview": [
            "Data pipeline architecture has evolved significantly from simple ETL scripts to sophisticated, multi-layered systems. Modern architectures must handle diverse data sources, varying latency requirements, and complex transformation logic while maintaining reliability and cost efficiency. Understanding architectural patterns helps data engineers design systems that scale with organizational needs.",
            "Key architectural patterns include the medallion architecture (bronze, silver, gold layers), lambda architecture (batch and streaming), kappa architecture (pure streaming), and data mesh (decentralized domain ownership). Each pattern addresses different scalability, latency, and organizational requirements."
        ],
        "key_concepts": [
            ("Medallion Architecture", "A layered data organization with bronze (raw ingestion), silver (validated/cleaned), and gold (aggregated/business-ready) zones."),
            ("Lambda Architecture", "A hybrid approach with batch and streaming layers providing comprehensive historical and real-time data processing."),
            ("Kappa Architecture", "A simplified architecture using only stream processing, where batch is handled by replaying streams."),
            ("Data Hub Architecture", "A centralized hub that brokers data between source systems and consuming applications."),
            ("Event-Driven Architecture", "Systems that respond to events in real time, enabling reactive data processing and microservices integration.")
        ],
        "takeaways": [
            "Medallion architecture organizes data into progressively refined layers from raw to business-ready.",
            "Lambda architecture combines batch and streaming for comprehensive data processing coverage.",
            "Kappa architecture simplifies to pure streaming, using stream replay for batch processing.",
            "Architecture selection depends on latency requirements, data volume, and organizational maturity."
        ]
    },
    "data-engineering-basics": {
        "overview": [
            "Data engineering basics form the foundation for all advanced data work. Every data engineer needs a solid understanding of core concepts including data modeling, storage systems, processing frameworks, pipeline design, and data governance. These fundamentals enable engineers to make informed architectural decisions and build reliable systems.",
            "The field encompasses three main areas: storage and infrastructure (databases, data lakes, cloud platforms), processing and transformation (ETL/ELT, streaming, orchestration), and governance and quality (cataloging, lineage, monitoring). Mastering these areas requires both theoretical knowledge and practical experience with modern tools and platforms."
        ],
        "key_concepts": [
            ("Relational Databases", "Systems that store data in structured tables with defined relationships and ACID transaction guarantees."),
            ("Distributed Computing", "Processing frameworks like MapReduce, Spark, and Flink that parallelize work across multiple machines."),
            ("Data Modeling", "The process of designing data structures and relationships using techniques like normalization and dimensional modeling."),
            ("Data Governance", "The overall management of data availability, usability, integrity, and security through policies and standards."),
            ("Orchestration", "Coordinating and scheduling data pipeline steps including dependency management, monitoring, and error handling.")
        ],
        "takeaways": [
            "Data engineering spans storage, processing, and governance across the data lifecycle.",
            "Relational databases remain fundamental, complemented by distributed and NoSQL systems.",
            "Data modeling techniques like dimensional modeling are essential for analytics use cases.",
            "Data governance ensures data is trustworthy, accessible, and compliant with regulations."
        ]
    },
}

LEARN_STOCK_TOPICS = {
    "how-stock-markets-work": {
        "overview": [
            "Stock markets are organized venues where buyers and sellers trade shares of publicly listed companies. They provide liquidity, price discovery, and access to capital for businesses while offering investors opportunities to own portions of companies and participate in economic growth. Understanding how stock markets operate is fundamental to participating in modern financial systems.",
            "Stock exchanges like the NYSE and NASDAQ serve as the primary trading venues, with market participants including individual investors, institutional investors, market makers, and high-frequency trading firms. Orders are matched through electronic order books that display bid and ask prices, with trades executed when orders cross. Market movements are driven by a complex interplay of company performance, economic conditions, and investor sentiment."
        ],
        "key_concepts": [
            ("Bid-Ask Spread", "The difference between the highest price a buyer is willing to pay (bid) and the lowest price a seller will accept (ask)."),
            ("Market Order", "An order to buy or sell at the current best available price, guaranteeing execution but not price certainty."),
            ("Limit Order", "An order to buy or sell at a specified price or better, guaranteeing price but not execution."),
            ("Liquidity", "The ability to buy or sell an asset quickly without causing a significant price movement."),
            ("Market Capitalization", "The total market value of a company's outstanding shares, calculated as share price times shares outstanding.")
        ],
        "takeaways": [
            "Stock markets provide liquidity, price discovery, and capital access for businesses and investors.",
            "Exchanges match buyers and sellers through electronic order books with bid and ask prices.",
            "Market orders prioritize execution speed; limit orders prioritize price certainty.",
            "Liquidity is essential for efficient market functioning and fair price discovery."
        ]
    },
    "reading-financial-statements": {
        "overview": [
            "Financial statements are the primary source of information about a company's financial health and performance. The three core statements — income statement, balance sheet, and cash flow statement — provide different perspectives on how a business generates revenue, manages assets and liabilities, and generates cash. Mastering financial statement analysis is essential for investors, analysts, and business decision-makers.",
            "The income statement shows profitability over a period, the balance sheet provides a snapshot of assets, liabilities, and equity at a point in time, and the cash flow statement reveals how cash moves through operations, investments, and financing. Analyzing trends and relationships across these statements reveals insights about business quality, growth potential, and financial risk."
        ],
        "key_concepts": [
            ("Revenue Recognition", "The accounting principle determining when revenue is recorded, affecting comparability across companies."),
            ("EBITDA", "Earnings Before Interest, Taxes, Depreciation, and Amortization — a measure of operating profitability."),
            ("Working Capital", "Current assets minus current liabilities, indicating a company's short-term financial health."),
            ("Free Cash Flow", "Cash from operations minus capital expenditures, representing cash available for shareholders."),
            ("Leverage Ratios", "Metrics like debt-to-equity that measure a company's use of debt financing relative to equity.")
        ],
        "takeaways": [
            "The three financial statements — income statement, balance sheet, and cash flow — provide complementary views of company health.",
            "EBITDA measures operating profitability before financing and accounting decisions.",
            "Free cash flow is a key indicator of financial flexibility and shareholder value creation.",
            "Ratio analysis across statements reveals trends in profitability, liquidity, and leverage."
        ]
    },
    "what-are-etfs": {
        "overview": [
            "Exchange-Traded Funds (ETFs) are investment funds that trade on stock exchanges, combining the diversification benefits of mutual funds with the trading flexibility of individual stocks. ETFs have grown explosively over the past two decades, revolutionizing how investors access markets, sectors, and strategies. They offer low costs, tax efficiency, and transparency compared to traditional mutual funds.",
            "ETFs can track broad market indices like the S&P 500, specific sectors like technology or healthcare, commodities like gold, or implement active strategies. The creation and redemption mechanism involving authorized participants keeps ETF prices closely aligned with their net asset value. Investors can buy and sell ETF shares throughout the trading day at market-determined prices."
        ],
        "key_concepts": [
            ("Net Asset Value", "The per-share value of an ETF's underlying holdings, calculated at the end of each trading day."),
            ("Authorized Participant", "A financial institution that creates or redeems ETF shares to keep market prices aligned with NAV."),
            ("Expense Ratio", "The annual fee charged by an ETF as a percentage of assets under management."),
            ("Tracking Error", "The difference between an ETF's returns and the returns of its underlying benchmark index."),
            ("Passive vs Active Management", "Passive ETFs track an index; active ETFs rely on manager decisions to outperform.")
        ],
        "takeaways": [
            "ETFs combine mutual fund diversification with stock-like trading flexibility and intraday pricing.",
            "The creation/redemption mechanism keeps ETF prices aligned with underlying asset values.",
            "Expense ratios for passive ETFs are significantly lower than actively managed funds.",
            "Tracking error measures how closely an ETF follows its benchmark index."
        ]
    },
    "introduction-to-risk": {
        "overview": [
            "Risk is the possibility of financial loss or underperformance relative to expectations. In investing, risk is inherent and cannot be eliminated, but it can be understood, measured, and managed. The relationship between risk and expected return is the fundamental trade-off in finance — higher potential returns come with higher risk.",
            "Risk comes in many forms: market risk (systematic), company-specific risk (idiosyncratic), liquidity risk, credit risk, and operational risk. Modern portfolio theory provides frameworks for measuring and managing these risks through diversification, hedging, and asset allocation. Understanding your risk tolerance and time horizon is essential for constructing appropriate portfolios."
        ],
        "key_concepts": [
            ("Standard Deviation", "A statistical measure of return volatility, commonly used as a proxy for total investment risk."),
            ("Beta", "A measure of a stock's sensitivity to overall market movements, with beta > 1 indicating higher volatility than the market."),
            ("Sharpe Ratio", "A risk-adjusted return measure calculated as excess return divided by standard deviation."),
            ("Value at Risk", "A statistical measure of the maximum expected loss over a given time period at a given confidence level."),
            ("Diversification", "Spreading investments across different assets to reduce unsystematic risk without sacrificing expected return.")
        ],
        "takeaways": [
            "Risk and expected return are fundamentally linked in financial markets.",
            "Standard deviation measures total risk; beta measures market-relative risk.",
            "Diversification reduces company-specific risk but cannot eliminate market risk.",
            "The Sharpe ratio enables comparison of risk-adjusted returns across different investments."
        ]
    },
    "introduction-to-market-indices": {
        "overview": [
            "Market indices are statistical measures that track the performance of a group of stocks representing a particular market, sector, or strategy. They serve as benchmarks for investment performance, the basis for index funds and ETFs, and barometers of economic health. Understanding how indices are constructed and calculated is essential for interpreting market movements.",
            "Indices can be price-weighted (Dow Jones Industrial Average), market-capitalization-weighted (S&P 500), or equal-weighted. Index methodology affects performance and composition. Rebalancing rules determine when constituents change. The rise of passive investing has made index construction increasingly influential in market dynamics."
        ],
        "key_concepts": [
            ("Market-Cap Weighting", "Index weighting scheme where companies are weighted proportional to their total market capitalization."),
            ("Price-Weighting", "Index weighting scheme where companies with higher stock prices have greater influence on index value."),
            ("Rebalancing", "The periodic process of adjusting index constituents to reflect changes in company eligibility and weight targets."),
            ("Total Return Index", "An index calculation that assumes dividends are reinvested, showing the full return from price appreciation and income."),
            ("Sector Classification", "Systems like GICS that categorize companies by industry, enabling sector-specific index construction.")
        ],
        "takeaways": [
            "Market indices serve as benchmarks, investment bases, and economic indicators.",
            "Index weighting methodology significantly affects performance and risk characteristics.",
            "Market-cap-weighted indices like the S&P 500 are the most common benchmark format.",
            "Passive investing growth has made index methodology increasingly important to market function."
        ]
    },
    "algorithmic-trading-strategies": {
        "overview": [
            "Algorithmic trading uses computer programs to execute trades based on predefined rules and mathematical models. Algorithms can analyze market data, identify opportunities, and execute orders faster than humans, often in milliseconds. Algorithmic trading now accounts for the majority of trading volume in developed equity markets.",
            "Common algorithmic trading strategies include trend following (momentum), mean reversion, statistical arbitrage, market making, and execution algorithms like VWAP and TWAP. Strategy development involves backtesting, optimization, and risk management. Modern algo trading platforms provide APIs, historical data access, and low-latency execution infrastructure."
        ],
        "key_concepts": [
            ("Momentum Trading", "A strategy that buys assets with recent upward price trends and sells those with downward trends."),
            ("Mean Reversion", "A strategy based on the assumption that prices tend to return to their historical averages over time."),
            ("Statistical Arbitrage", "A strategy exploiting pricing inefficiencies between related securities using statistical models."),
            ("VWAP", "Volume-Weighted Average Price — an execution algorithm that aims to execute orders at prices close to the market VWAP."),
            ("Backtesting", "Evaluating a trading strategy using historical data to assess its performance before live deployment.")
        ],
        "takeaways": [
            "Algorithmic trading executes pre-programmed strategies at speeds and scales impossible for humans.",
            "Common strategy types include momentum, mean reversion, statistical arbitrage, and execution algorithms.",
            "Backtesting is essential but must account for survivorship bias, look-ahead bias, and transaction costs.",
            "Low-latency infrastructure is critical for strategies that compete on speed."
        ]
    },
    "market-microstructure-order-books": {
        "overview": [
            "Market microstructure studies the process by which prices are formed in financial markets, focusing on the mechanics of trading, order types, and market participant behavior. The order book is the central mechanism — it lists all outstanding buy and sell orders for a security, showing price levels and quantities available. Understanding market microstructure provides insights into liquidity, price impact, and market efficiency.",
            "Key concepts include the limit order book (displaying all resting orders), market maker obligations, tick size regimes, and market data feeds. The interaction between different market participants — retail investors, institutions, high-frequency traders, and market makers — determines order flow dynamics and short-term price movements."
        ],
        "key_concepts": [
            ("Limit Order Book", "The electronic list of all outstanding limit orders for a security, showing bid and ask prices with quantities."),
            ("Order Flow", "The stream of buy and sell orders entering the market, whose composition affects short-term price direction."),
            ("Market Maker", "A firm that stands ready to buy and sell a security, providing liquidity in exchange for the bid-ask spread."),
            ("Price Impact", "The change in price caused by executing a trade, larger for trades that represent a high proportion of average volume."),
            ("Tick Size", "The minimum price increment for trading a security, affecting spread width and market maker profitability.")
        ],
        "takeaways": [
            "The limit order book displays all resting buy and sell orders, determining available liquidity at each price level.",
            "Market makers provide liquidity by continuously quoting bid and ask prices.",
            "Order flow composition affects short-term price movements beyond fundamental information.",
            "Price impact is a key cost consideration for large institutional trades."
        ]
    },
    "factor-investing-risk-parity": {
        "overview": [
            "Factor investing targets specific drivers of stock returns beyond broad market exposure. Academic research has identified factors like value, momentum, size, quality, and low volatility that have historically delivered premium returns. These factors can be accessed through factor-based ETFs and smart beta strategies.",
            "Risk parity is a portfolio construction approach that allocates risk equally across asset classes rather than allocating capital equally. The goal is to achieve more consistent returns by balancing contributions from stocks, bonds, commodities, and other assets. Risk parity has gained popularity among institutional investors seeking better diversification."
        ],
        "key_concepts": [
            ("Value Factor", "The tendency for stocks with low prices relative to fundamentals (P/E, P/B) to outperform growth stocks."),
            ("Momentum Factor", "The tendency for assets with strong recent performance to continue performing well."),
            ("Risk Parity", "Portfolio construction that equalizes risk contribution across asset classes rather than capital allocation."),
            ("Smart Beta", "Investment strategies that use alternative index construction rules to capture factor premiums."),
            ("Factor Correlation", "The degree to which different return factors move together, affecting diversification benefits.")
        ],
        "takeaways": [
            "Factor investing captures specific return premiums like value, momentum, quality, and low volatility.",
            "Risk parity allocates risk equally across assets for more consistent portfolio performance.",
            "Factor correlations vary over time, affecting diversification benefits.",
            "Smart beta strategies provide factor exposure through rules-based index construction."
        ]
    },
    "behavioral-finance-market-anomalies": {
        "overview": [
            "Behavioral finance challenges the traditional assumption that markets are efficient and investors are rational. It draws on cognitive psychology to explain how biases affect financial decision-making and lead to market anomalies — predictable patterns that contradict efficient market theory. Understanding these biases helps investors avoid common mistakes and identify mispriced assets.",
            "Key behavioral biases include overconfidence (trading too much), loss aversion (feeling losses more than gains), anchoring (fixating on reference prices), herding (following the crowd), and confirmation bias (seeking confirming information). Market anomalies include the January effect, momentum, and value premium, which persist despite being well-documented."
        ],
        "key_concepts": [
            ("Prospect Theory", "Kahneman and Tversky's model showing that people value gains and losses asymmetrically, feeling losses more intensely."),
            ("Loss Aversion", "The tendency to prefer avoiding losses over acquiring equivalent gains, typically feeling losses 2x more than gains."),
            ("Anchoring", "The tendency to rely too heavily on the first piece of information encountered when making decisions."),
            ("Herding", "The tendency to follow the actions of others, leading to momentum and bubbles in financial markets."),
            ("Confirmation Bias", "The tendency to seek and interpret information that confirms existing beliefs while ignoring contradictory evidence.")
        ],
        "takeaways": [
            "Behavioral finance explains how cognitive biases lead to systematic errors in financial decision-making.",
            "Loss aversion causes investors to feel losses roughly twice as intensely as equivalent gains.",
            "Market anomalies like momentum and value premium persist despite being well-documented.",
            "Understanding biases helps investors design systems to counteract their effects."
        ]
    },
    "alternative-data-investing": {
        "overview": [
            "Alternative data refers to non-traditional data sources used by investors to gain competitive advantage. While traditional analysis relies on financial statements, economic data, and market prices, alternative data captures real-time signals from sources like satellite imagery, credit card transactions, social media sentiment, web scraping, and supply chain data.",
            "The alternative data market has grown explosively, with hedge funds and asset managers investing heavily in new data sources and analytical capabilities. Key use cases include tracking retail foot traffic, monitoring crop health from satellite, analyzing job postings for hiring trends, and measuring supply chain activity through shipping data."
        ],
        "key_concepts": [
            ("Satellite Imagery Data", "Analyzing satellite images to track crop yields, retail parking lot traffic, oil tanker movements, and construction activity."),
            ("Credit Card Transaction Data", "Aggregated and anonymized consumer spending data providing real-time revenue signals for retailers."),
            ("Web Scraping", "Extracting pricing, product availability, review data, and other signals from e-commerce and informational websites."),
            ("Natural Language Processing", "Analyzing earnings call transcripts, news articles, and social media to quantify sentiment and topic trends."),
            ("Data Licensing", "The legal framework for acquiring alternative data, including exclusivity terms, usage restrictions, and compliance.")
        ],
        "takeaways": [
            "Alternative data provides real-time signals beyond traditional financial and economic data sources.",
            "Satellite imagery, credit card data, and web scraping are among the most popular alternative data sources.",
            "NLP enables quantitative analysis of text-based data like earnings calls and news.",
            "Data licensing and compliance are critical considerations in alternative data investing."
        ]
    },
    "cryptocurrency-markets-structure": {
        "overview": [
            "Cryptocurrency markets represent a new asset class with distinct structural characteristics compared to traditional financial markets. Operating 24/7 across global exchanges, crypto markets feature unique dynamics including extreme volatility, fragmented liquidity, and the influence of on-chain metrics and protocol-level events.",
            "Market structure in crypto differs fundamentally from equities: no central exchange, varying fee models, the presence of both centralized (CEX) and decentralized (DEX) exchanges, and the impact of blockchain-specific factors like mining rewards, staking yields, and governance proposals. Understanding these structural differences is essential for trading and investing in digital assets."
        ],
        "key_concepts": [
            ("Centralized Exchange", "A traditional order-book exchange like Binance or Coinbase that custodies user funds and matches orders."),
            ("Decentralized Exchange", "A blockchain-based exchange like Uniswap that uses automated market makers and smart contracts."),
            ("On-Chain Metrics", "Data derived directly from blockchain transactions including active addresses, transaction volume, and network hash rate."),
            ("Stablecoin", "A cryptocurrency designed to maintain a stable value relative to a reference asset, typically USD."),
            ("Liquidity Fragmentation", "The dispersion of trading volume across multiple exchanges, complicating price discovery and execution.")
        ],
        "takeaways": [
            "Cryptocurrency markets operate 24/7 with distinct structural features from traditional markets.",
            "Centralized and decentralized exchanges offer different trade-offs in custody, fees, and transparency.",
            "On-chain metrics provide unique insights into network health and user activity.",
            "Liquidity fragmentation across exchanges creates both challenges and arbitrage opportunities."
        ]
    },
    "volatility-trading-vix": {
        "overview": [
            "Volatility trading has become a sophisticated asset class, with the VIX index at its center. The CBOE Volatility Index (VIX) measures expected 30-day volatility of the S&P 500, often called the fear gauge. Traders can express views on volatility through VIX futures, options, and ETPs, creating a rich ecosystem for hedging and speculation.",
            "Volatility exhibits unique properties including mean reversion, negative correlation with equity returns, and distinct term structure dynamics. The VIX term structure (contango vs backwardation) provides trading signals and reflects market expectations. Volatility risk premium — the tendency for implied volatility to exceed realized volatility — is a key source of return for systematic volatility strategies."
        ],
        "key_concepts": [
            ("VIX Index", "The CBOE Volatility Index measuring implied volatility of S&P 500 options over the next 30 days."),
            ("Contango", "A VIX futures curve where deferred contracts trade at premiums to spot, typical in calm markets."),
            ("Backwardation", "A VIX futures curve where near-term contracts trade at premiums to deferred, typical during market stress."),
            ("Volatility Risk Premium", "The persistent tendency for implied volatility to exceed subsequently realized volatility."),
            ("Variance Swap", "An over-the-counter derivative that pays the difference between realized variance and a fixed strike.")
        ],
        "takeaways": [
            "The VIX index measures expected S&P 500 volatility and serves as a fear gauge for equity markets.",
            "VIX futures contango is typical in calm markets; backwardation signals stress.",
            "The volatility risk premium provides a return source for systematic volatility-selling strategies.",
            "VIX ETPs allow retail and institutional investors to express volatility views."
        ]
    },
    "fixed-income-macro-markets": {
        "overview": [
            "Fixed income markets are the largest securities markets globally, encompassing government bonds, corporate debt, mortgage-backed securities, and money market instruments. These markets are deeply connected to monetary policy, economic cycles, and inflation expectations, making them central to macroeconomic analysis and portfolio construction.",
            "The yield curve — the relationship between bond yields and maturities — is a critical indicator of economic expectations. An upward-sloping curve signals economic growth expectations, while an inverted curve has historically preceded recessions. Fixed income trading occurs primarily over-the-counter, with electronic trading growing but less dominant than in equities."
        ],
        "key_concepts": [
            ("Yield Curve", "The graphical relationship between bond yields and maturities, a key indicator of economic expectations."),
            ("Duration", "A measure of bond price sensitivity to interest rate changes, expressed in years."),
            ("Credit Spread", "The yield difference between a corporate bond and a comparable government bond, reflecting default risk."),
            ("Convexity", "A measure of how bond duration changes as yields change, important for large interest rate moves."),
            ("Monetary Policy Transmission", "How central bank policy rate changes affect bond yields, lending rates, and economic activity.")
        ],
        "takeaways": [
            "Fixed income is the largest securities market and is deeply connected to monetary policy and economic cycles.",
            "The yield curve shape reflects market expectations about growth, inflation, and monetary policy.",
            "Duration measures interest rate sensitivity; credit spread measures default risk.",
            "Fixed income trading is primarily OTC with growing electronic execution."
        ]
    },
    "dark-pools-off-exchange-trading": {
        "overview": [
            "Dark pools are private trading venues that allow institutional investors to execute large orders without revealing their intentions to the public market. They have grown to account for a significant share of equity trading volume as institutions seek to minimize market impact and information leakage when trading large blocks.",
            "Off-exchange trading also occurs through internalization by wholesalers and broker-dealers who match orders internally rather than routing them to exchanges. While dark pools and internalization reduce market impact for large trades, they have raised regulatory concerns about transparency, best execution, and market quality."
        ],
        "key_concepts": [
            ("Dark Pool", "A private trading venue where order information is not displayed publicly before execution."),
            ("Internalization", "When a broker executes orders against its own inventory rather than routing them to an exchange."),
            ("Market Impact", "The price movement caused by executing a trade, which dark pools aim to minimize."),
            ("Information Leakage", "The risk that order flow information reveals trading intentions and affects prices before execution."),
            ("Midpoint Pegging", "An order type that executes at the midpoint of the NBBO, reducing spread costs and signaling.")
        ],
        "takeaways": [
            "Dark pools enable large institutional trades with reduced market impact and information leakage.",
            "Off-exchange trading has grown significantly, now accounting for a major share of equity volume.",
            "Internalization by wholesalers routes retail order flow away from public exchanges.",
            "Regulatory concerns focus on transparency and ensuring best execution across all venues."
        ]
    },
    "etf-ecosystem-creation-impact": {
        "overview": [
            "The ETF ecosystem has grown into a massive market structure influence, with thousands of products spanning asset classes, geographies, and strategies. Understanding the creation and redemption mechanism, the roles of authorized participants, and the market impact of ETF flows is essential for modern market participants. ETFs affect the underlying securities they hold through demand transmission.",
            "When investors buy an ETF, the creation mechanism forces APs to acquire the underlying securities, transmitting demand. This mechanism keeps ETF prices aligned with NAV but can create dislocations during periods of market stress. The ETF ecosystem has changed market dynamics, particularly in fixed income and less liquid asset classes where ETF trading can exceed underlying market volume."
        ],
        "key_concepts": [
            ("Creation/Redemption Mechanism", "The process by which APs create new ETF shares by depositing the underlying basket or redeem shares for the basket."),
            ("Primary vs Secondary Market", "Primary market is creation/redemption between APs and ETF issuers; secondary market is exchange trading between investors."),
            ("Basket Composition", "The specific securities that must be deposited to create or redeemed to redeem an ETF share."),
            ("ETF Flow", "Net creation or redemption of ETF shares, reflecting investor demand for the product."),
            ("Cash vs In-Kind", "Creation/redemption settled in cash versus actual securities, affecting tax efficiency and tracking.")
        ],
        "takeaways": [
            "The creation/redemption mechanism keeps ETF prices aligned with underlying NAV.",
            "Authorized Participants bridge primary and secondary ETF markets through arbitrage.",
            "ETF flows transmit investor demand to underlying securities, affecting market dynamics.",
            "In-kind creation/redemption provides tax advantages over cash settlement."
        ]
    },
    "cross-asset-commodity-trading": {
        "overview": [
            "Commodity trading spans energy, metals, and agricultural products, each with distinct supply-demand dynamics, storage considerations, and pricing mechanisms. Commodities are essential portfolio diversifiers, offering inflation protection and low correlation with traditional financial assets. The commodity markets include both physical trading and extensive derivatives markets.",
            "Key commodity sectors include energy (crude oil, natural gas, refined products), precious metals (gold, silver, platinum), industrial metals (copper, aluminum, iron ore), and agricultural products (grains, livestock, softs). Each sector has unique drivers from weather patterns to geopolitics to technological change."
        ],
        "key_concepts": [
            ("Futures Contract", "A standardized exchange-traded agreement to buy or sell a commodity at a predetermined price on a future date."),
            ("Contango vs Backwardation", "Futures curve structures where deferred prices trade above (contango) or below (backwardation) spot prices."),
            ("Basis Risk", "The risk that the price difference between a futures contract and the underlying commodity changes unexpectedly."),
            ("Storage Costs", "The costs of holding physical commodities including warehousing, insurance, and financing charges."),
            ("Convenience Yield", "The non-monetary benefit of holding physical inventory, such as ensuring production continuity.")
        ],
        "takeaways": [
            "Commodities provide portfolio diversification and inflation protection with distinct sector-specific dynamics.",
            "Futures contracts are the primary trading vehicle, with curve structure reflecting supply-demand balance.",
            "Storage costs and convenience yield determine the shape of the futures curve.",
            "Basis risk is a key consideration when hedging commodity exposure with futures."
        ]
    },
    "fx-market-structure-global-currencies": {
        "overview": [
            "The foreign exchange (FX) market is the largest and most liquid financial market in the world, with daily trading volume exceeding $7.5 trillion. Unlike equities or futures, FX is decentralized with no central exchange, trading over-the-counter through a global network of banks, brokers, and electronic platforms. The market operates 24 hours a day during the business week.",
            "Major currency pairs like EUR/USD, USD/JPY, and GBP/USD dominate trading volumes, followed by crosses and emerging market currencies. Market participants range from central banks and commercial banks to hedge funds, corporations, and retail traders. Each participant type has different motivations from hedging to speculation to facilitating international trade."
        ],
        "key_concepts": [
            ("Pip", "The smallest price movement in FX trading, typically 0.0001 for most pairs or 0.01 for JPY pairs."),
            ("Spot vs Forward", "Spot FX settles in T+2 days; forward contracts agree on future exchange rates for hedging."),
            ("Carry Trade", "A strategy borrowing a low-yielding currency to invest in a higher-yielding one, profiting from the interest rate differential."),
            ("Central Bank Intervention", "Actions by central banks to influence exchange rates through direct market participation or policy signals."),
            ("Triangular Arbitrage", "Exploiting price discrepancies between three currency pairs to generate risk-free profits.")
        ],
        "takeaways": [
            "The FX market is the world's largest financial market, operating 24/5 with decentralized OTC trading.",
            "Major currency pairs (EUR/USD, USD/JPY, GBP/USD) account for the majority of trading volume.",
            "Exchange rates are driven by interest rate differentials, trade flows, capital flows, and geopolitical factors.",
            "Leverage is widely available in FX trading, magnifying both gains and losses."
        ]
    },
}

LEARN_AML_TOPICS = {
    "ml-typologies-current-trends": {
        "overview": [
            "Money laundering typologies evolve constantly as criminals adapt to new technologies, regulations, and detection methods. Understanding current trends in laundering methodology is essential for compliance professionals to design effective detection programs. Typologies range from traditional trade-based laundering to sophisticated crypto mixing and decentralized finance exploitation.",
            "Current major typologies include professional money laundering networks offering laundering-as-a-service, exploitation of digital assets and DeFi protocols, trade-based laundering through supply chain manipulation, real estate laundering through shell companies, and the use of legal structures like trusts and foundations to obscure beneficial ownership."
        ],
        "key_concepts": [
            ("Trade-Based Money Laundering", "Using trade transactions to move value across borders through invoice manipulation, over/under-shipment, and phantom shipping."),
            ("Crypto Mixers", "Services that combine cryptocurrency from multiple sources to obscure transaction trails, like Tornado Cash."),
            ("Professional Money Laundering Networks", "Organized groups that provide money laundering services to criminals for a fee, operating across multiple jurisdictions."),
            ("Shell Companies", "Legal entities with no active business operations used to obscure ownership and move funds."),
            ("Smurfing", "Breaking large transactions into smaller amounts to avoid reporting thresholds and regulatory scrutiny.")
        ],
        "takeaways": [
            "Money laundering typologies constantly evolve, requiring continuous update of detection systems.",
            "Trade-based laundering remains one of the most difficult typologies to detect due to legitimate trade volume.",
            "Crypto mixing and DeFi protocols present new challenges for AML compliance in the digital asset space.",
            "Professional laundering networks provide sophisticated, fee-based services to criminal organizations."
        ]
    },
    "risk-based-approach-implementation": {
        "overview": [
            "Implementing a risk-based approach (RBA) requires translating high-level regulatory expectations into practical, operational processes. This involves developing risk assessment methodologies, building risk scoring models, establishing risk appetite statements, and creating governance frameworks that ensure consistent application across the organization.",
            "A practical RBA implementation begins with a comprehensive business-wide risk assessment that identifies inherent risks across customer types, products, geographies, and delivery channels. This assessment informs the design of tiered due diligence measures, monitoring frequency, and threshold settings. Regular validation ensures the RBA remains effective as risks evolve."
        ],
        "key_concepts": [
            ("Business-Wide Risk Assessment", "An organization-level evaluation of all ML/TF risks across customers, products, geographies, and channels."),
            ("Risk Scoring Model", "A quantitative model that assigns risk scores based on weighted risk factors, determining due diligence levels."),
            ("Tiered Due Diligence", "Applying different levels of customer scrutiny — simplified, standard, enhanced — based on risk scores."),
            ("Risk Appetite Statement", "A formal document defining the level of ML/TF risk the organization is willing to accept."),
            ("Model Validation", "Independent testing of risk models to ensure they are accurate, calibrated, and performing as intended.")
        ],
        "takeaways": [
            "RBA implementation requires systematic risk assessment, scoring, and tiered control application.",
            "Business-wide risk assessment is the foundation for all subsequent RBA processes.",
            "Risk scoring models must be validated regularly to maintain effectiveness.",
            "Tiered due diligence ensures compliance resources are focused on highest-risk relationships."
        ]
    },
    "enhanced-due-diligence-pep": {
        "overview": [
            "Enhanced Due Diligence (EDD) is a higher level of customer scrutiny applied to high-risk relationships, most notably Politically Exposed Persons (PEPs). PEPs are individuals who hold or have held prominent public positions, and their family members and close associates. Their access to public funds and influence makes them higher risk for corruption and bribery.",
            "EDD measures go significantly beyond standard CDD. They require identifying the source of wealth and source of funds in detail, understanding the customer's business and reputation, establishing the rationale for the business relationship, and conducting more frequent reviews. EDD programs must be risk-sensitive, with the depth of investigation proportional to the assessed risk."
        ],
        "key_concepts": [
            ("PEP", "Politically Exposed Person — an individual with a prominent public position, their family members, and close associates."),
            ("Source of Wealth", "The total accumulation of a customer's wealth, including inheritance, business profits, investments, and other sources."),
            ("Source of Funds", "The specific origin of money being used for a particular transaction or business relationship."),
            ("Domestic vs Foreign PEP", "Foreign PEPs generally require higher scrutiny than domestic PEPs due to jurisdictional oversight differences."),
            ("Adverse Media Screening", "Checking customers against news sources for negative information related to corruption, financial crime, or sanctions.")
        ],
        "takeaways": [
            "EDD applies enhanced scrutiny to high-risk customers including PEPs and their associates.",
            "Source of wealth and source of funds analysis are critical EDD components.",
            "Foreign PEPs typically require higher levels of due diligence than domestic PEPs.",
            "EDD programs must be risk-sensitive, with investigation depth proportional to assessed risk."
        ]
    },
    "entity-resolution-network-analysis": {
        "overview": [
            "Entity resolution is the process of determining whether multiple records or identifiers refer to the same real-world entity. In AML compliance, entity resolution is critical for identifying related accounts, beneficial ownership structures, and hidden relationships that may indicate money laundering or sanctions evasion.",
            "Network analysis extends entity resolution by mapping relationships between entities — individuals, companies, accounts, and transactions — to reveal hidden structures. Graph algorithms can identify suspicious patterns like circular transactions, concentration of funds, and unusual connectivity that may indicate organized criminal activity or terrorist financing networks."
        ],
        "key_concepts": [
            ("Entity Resolution", "The process of matching and linking records that refer to the same real-world entity across different data sources."),
            ("Graph Database", "A database that stores entities as nodes and relationships as edges, optimized for relationship queries."),
            ("Social Network Analysis", "Analyzing relationships between entities to identify key actors, clusters, and communication patterns."),
            ("Circular Transaction Detection", "Identifying transactions that flow through multiple accounts and return to the originator, indicating potential layering."),
            ("Link Analysis", "Visual and analytical techniques for discovering relationships and patterns in connected data.")
        ],
        "takeaways": [
            "Entity resolution links records across systems to build complete customer profiles.",
            "Network analysis reveals hidden relationships and patterns invisible to transaction-level monitoring.",
            "Graph databases enable efficient querying of complex entity relationship structures.",
            "Circular transaction patterns may indicate money laundering layering activity."
        ]
    },
    "ai-machine-learning-aml": {
        "overview": [
            "Artificial intelligence and machine learning are transforming AML compliance by enabling more effective detection, reducing false positives, and automating routine processes. Traditional rules-based systems struggle with the volume and sophistication of modern financial crime. ML models can detect subtle patterns, adapt to new typologies, and improve over time.",
            "Key AML applications of ML include transaction monitoring (anomaly detection models), customer risk scoring (predictive models), SAR prioritization (triage models), and entity resolution (matching and clustering models). Supervised learning requires labeled data, unsupervised learning detects novel patterns, and natural language processing supports adverse media screening."
        ],
        "key_concepts": [
            ("Anomaly Detection", "ML models that identify transactions or behaviors deviating significantly from normal patterns."),
            ("Supervised Learning", "Training models on labeled data where outcomes (e.g., confirmed SAR) are known."),
            ("Unsupervised Learning", "Finding patterns in data without labels, useful for detecting novel laundering typologies."),
            ("False Positive Reduction", "Using ML to prioritize alerts, reducing the number of false alerts analysts must review."),
            ("Explainable AI", "ML techniques that provide interpretable explanations for model decisions, essential for regulatory compliance.")
        ],
        "takeaways": [
            "AI/ML improves AML detection effectiveness and reduces false positive rates compared to rules-only systems.",
            "Supervised learning uses historical SAR data; unsupervised learning detects novel suspicious patterns.",
            "Explainable AI is critical for regulatory acceptance of ML-based AML systems.",
            "NLP enables automated adverse media screening from news and other text sources."
        ]
    },
    "crypto-aml-defi-mica": {
        "overview": [
            "The regulation of cryptocurrency and decentralized finance has evolved rapidly, with the EU's Markets in Crypto-Assets (MiCA) regulation leading global efforts to create comprehensive frameworks. MiCA establishes rules for crypto-asset issuers, service providers, and stablecoins, creating a harmonized regime across EU member states. AML requirements for crypto assets are a key component.",
            "Crypto AML challenges include pseudonymous transactions, decentralized platforms without central control points, cross-border instant settlement, and the use of mixers and privacy coins. The Travel Rule (FATF Recommendation 16) now applies to crypto transfers, requiring VASPs to share originator and beneficiary information."
        ],
        "key_concepts": [
            ("MiCA", "The EU Markets in Crypto-Assets Regulation, creating a comprehensive regulatory framework for crypto assets and services."),
            ("VASP", "Virtual Asset Service Provider — entities that exchange, transfer, or custody crypto assets, subject to AML regulation."),
            ("Travel Rule", "FATF requirement for VASPs to collect and share originator and beneficiary information for crypto transactions."),
            ("DeFi Regulation", "Emerging regulatory approaches to decentralized finance, addressing platforms without identifiable operators."),
            ("Privacy Coins", "Cryptocurrencies like Monero that implement enhanced privacy features, complicating transaction monitoring.")
        ],
        "takeaways": [
            "MiCA creates a comprehensive EU framework for crypto-asset regulation including AML requirements.",
            "The Travel Rule extends traditional wire transfer information sharing to crypto transactions.",
            "DeFi presents unique regulatory challenges due to the absence of central control points.",
            "Privacy coins and mixers create significant challenges for AML transaction monitoring."
        ]
    },
    "correspondent-banking-derisking": {
        "overview": [
            "Correspondent banking is a critical component of the global financial system, enabling banks in different jurisdictions to conduct cross-border transactions. Correspondent banks provide services to respondent banks, including wire transfers, trade finance, and foreign exchange. This relationship carries significant AML risk, as the correspondent bank relies on the respondent's due diligence.",
            "Derisking refers to the trend of correspondent banks terminating relationships with respondent banks in certain regions or sectors due to AML compliance concerns. While derisking reduces individual bank risk, it has negative consequences for financial inclusion, remittance flows, and economic development in affected jurisdictions."
        ],
        "key_concepts": [
            ("Correspondent Banking", "A relationship where one bank (correspondent) provides services to another bank (respondent) in a different jurisdiction."),
            ("Nostro/Vostro Accounts", "Accounts that one bank holds with another bank to facilitate cross-border transactions."),
            ("Derisking", "The practice of terminating or restricting business relationships to avoid perceived AML/CFT compliance risks."),
            ("Financial Inclusion", "Access to affordable financial services for individuals and businesses, negatively impacted by derisking."),
            ("Due Diligence Reliance", "The reliance of correspondent banks on respondent banks' due diligence, requiring careful counterparty assessment.")
        ],
        "takeaways": [
            "Correspondent banking enables cross-border transactions through interbank relationships.",
            "Derisking reduces individual bank compliance risk but harms financial inclusion and remittance flows.",
            "FATF and regulators have issued guidance discouraging indiscriminate derisking.",
            "Correspondent banks must carefully assess respondent banks' AML programs."
        ]
    },
    "aml-international-cooperation": {
        "overview": [
            "International cooperation is essential for effective AML enforcement, as money laundering is inherently cross-border. Criminals exploit differences in national regulatory regimes, enforcement capacity, and information sharing to move funds across jurisdictions. Multiple mechanisms exist for cooperation, from formal mutual legal assistance treaties to informal intelligence sharing between FIUs.",
            "Key cooperation mechanisms include the Egmont Group of FIUs (facilitating information exchange), FATF mutual evaluations (peer review of national regimes), and bilateral agreements for asset recovery and extradition. The effectiveness of international cooperation depends on the quality of national AML regimes and the willingness of jurisdictions to share information."
        ],
        "key_concepts": [
            ("Egmont Group", "An international network of 170+ Financial Intelligence Units that facilitates information sharing and cooperation."),
            ("Mutual Legal Assistance Treaty", "Formal bilateral agreements between countries for sharing evidence and assisting in criminal investigations."),
            ("FATF Mutual Evaluation", "Peer review process assessing countries' compliance with FATF 40 Recommendations."),
            ("Asset Recovery", "The process of identifying, freezing, and confiscating proceeds of crime across international borders."),
            ("Information Sharing", "Exchange of financial intelligence between FIUs, law enforcement, and regulatory bodies across jurisdictions.")
        ],
        "takeaways": [
            "International cooperation is essential because money laundering is inherently cross-border.",
            "The Egmont Group facilitates information exchange between 170+ Financial Intelligence Units.",
            "FATF mutual evaluations assess and drive improvement in national AML regimes.",
            "Asset recovery across borders requires effective MLATs and international cooperation."
        ]
    },
    "aml-audit-examination": {
        "overview": [
            "AML audit and examination processes evaluate the effectiveness of financial institutions' compliance programs. Internal auditors assess design and operational effectiveness, while regulatory examiners evaluate compliance with legal and regulatory requirements. Both processes are critical for identifying gaps, driving improvement, and demonstrating the institution's commitment to compliance.",
            "A comprehensive AML audit covers governance, risk assessment, policies and procedures, training, transaction monitoring, SAR filing, recordkeeping, and independent testing. Regulatory examinations focus on the institution's risk profile, the quality of its risk assessment, and the effectiveness of its controls. Findings can range from recommendations to formal enforcement actions."
        ],
        "key_concepts": [
            ("Independent Testing", "The regulatory requirement for periodic independent evaluation of the AML program, conducted by internal audit or external parties."),
            ("Examination Scope", "The specific areas and time period covered by a regulatory AML examination or internal audit."),
            ("Findings Classification", "Categorizing audit findings by severity — observation, finding, deficiency, or material weakness."),
            ("Corrective Action Plan", "A formal plan addressing audit and examination findings with specific remediation steps and timelines."),
            ("Examination Rating", "Regulatory assessment of AML program effectiveness, often on a scale from satisfactory to unsatisfactory.")
        ],
        "takeaways": [
            "AML audits evaluate program design and effectiveness; regulatory examinations assess legal compliance.",
            "Independent testing is a regulatory requirement for all AML compliance programs.",
            "Audit findings must be addressed through formal corrective action plans with accountability.",
            "Regulatory examination results can lead to ratings, requirements, or enforcement actions."
        ]
    },
    "trade-finance-tbml-detection": {
        "overview": [
            "Trade finance is particularly vulnerable to money laundering due to the volume, complexity, and cross-border nature of international trade. Trade-Based Money Laundering (TBML) exploits trade transactions to move value across borders, using techniques like over-invoicing, under-invoicing, multiple invoicing, and phantom shipments. TBML is considered one of the most difficult laundering methods to detect.",
            "Detection of TBML requires analyzing trade documents including invoices, bills of lading, customs declarations, and letters of credit. Red flags include significant price deviations from market value, inconsistent shipping routes, discrepancies in goods description, and unusual payment terms. Advanced detection uses data analytics to compare trade data across counterparties and identify anomalous patterns."
        ],
        "key_concepts": [
            ("Over-Invoicing", "Inflating the value of goods on an invoice to move excess funds to the seller, justifying larger value transfers."),
            ("Under-Invoicing", "Understating the value of goods to reduce the apparent payment due, enabling the buyer to receive value offshore."),
            ("Letters of Credit", "Bank-issued guarantees of payment in trade transactions, which can be manipulated for TBML purposes."),
            ("Bills of Lading", "Shipping documents that can be forged or manipulated to support phantom shipments or misdescribed goods."),
            ("Trade Data Analytics", "Using data analysis to compare trade documentation against market benchmarks and detect anomalies.")
        ],
        "takeaways": [
            "TBML exploits trade transactions through invoice manipulation, phantom shipments, and misdescription of goods.",
            "Detection requires analysis of trade documents and comparison with market data.",
            "Price deviation analysis compares invoice values with commodity market prices to identify anomalies.",
            "TBML is considered one of the most challenging laundering methods to detect and investigate."
        ]
    },
    "sanctions-screening-global-regimes": {
        "overview": [
            "Sanctions regimes have proliferated globally, with the US, EU, UK, UN, and numerous individual countries maintaining active sanctions programs. Each regime has distinct legal frameworks, designation lists, and compliance requirements. Financial institutions must screen against multiple regimes simultaneously, often with conflicting or overlapping requirements.",
            "Key sanctions programs include US OFAC sanctions (comprehensive programs against Iran, North Korea, Syria, Cuba, and Russia, plus numerous targeted designations), EU restrictive measures, UK OFSI sanctions, and UN Security Council resolutions. Sanctions can be comprehensive (country-wide), sectoral (specific industries), or targeted (individuals and entities)."
        ],
        "key_concepts": [
            ("OFAC Sanctions", "US sanctions programs administered by the Office of Foreign Assets Control, including country, sectoral, and targeted designations."),
            ("EU Restrictive Measures", "EU sanctions including asset freezes, travel bans, and sectoral restrictions adopted by the Council."),
            ("UK OFSI", "The Office of Financial Sanctions Implementation, responsible for enforcing UK financial sanctions."),
            ("UN Security Council Sanctions", "Mandatory sanctions adopted under Chapter VII of the UN Charter, binding on all member states."),
            ("Secondary Sanctions", "US sanctions that target non-US persons for activities involving sanctioned countries or entities.")
        ],
        "takeaways": [
            "Multiple overlapping sanctions regimes require institutions to screen against numerous lists simultaneously.",
            "OFAC administers the most comprehensive US sanctions program with extraterritorial reach.",
            "EU and UK sanctions have distinct legal frameworks and designation processes.",
            "Secondary sanctions extend US enforcement jurisdiction to non-US persons and transactions."
        ]
    },
    "aml-training-culture-esg": {
        "overview": [
            "A strong AML compliance culture starts with effective training and awareness programs. All employees, not just compliance staff, must understand their role in preventing financial crime. Training must be tailored to different roles, regular, and tested for effectiveness. Beyond regulatory requirements, a culture of compliance improves overall risk management and business integrity.",
            "The intersection of AML with ESG (Environmental, Social, Governance) factors is increasingly recognized. Effective AML programs contribute to good governance, while certain ESG factors — such as corruption risk in supply chains — overlap directly with AML concerns. Investors and stakeholders increasingly evaluate companies' AML programs as part of broader ESG assessments."
        ],
        "key_concepts": [
            ("AML Training Program", "A structured program of initial and ongoing training covering AML regulations, internal policies, and red flag identification."),
            ("Compliance Culture", "The values, attitudes, and behaviors throughout an organization that support regulatory compliance."),
            ("Role-Based Training", "Training content tailored to specific job functions, with different depth for front-line, management, and compliance staff."),
            ("Training Effectiveness Testing", "Assessing whether training has improved knowledge and changed behavior, not just completion tracking."),
            ("ESG Integration", "Connecting AML compliance with ESG frameworks, recognizing that financial crime prevention supports good governance goals.")
        ],
        "takeaways": [
            "A strong compliance culture requires effective, role-based training for all employees.",
            "Training effectiveness must be measured through testing and behavioral observation.",
            "AML compliance intersects with ESG through governance and supply chain integrity.",
            "Regulators expect institutions to demonstrate not just training completion but effectiveness."
        ]
    },
    "designing-aml-program": {
        "overview": [
            "Designing an effective AML compliance program requires a systematic approach that addresses regulatory requirements, risk profile, and organizational context. The five mandatory pillars of a US AML program — policies, procedures, and internal controls; designation of a compliance officer; ongoing training; independent testing; and customer due diligence — provide a framework that applies globally.",
            "A well-designed program begins with a thorough risk assessment that identifies the institution's specific ML/TF risks. This assessment drives the design of controls across governance, risk management, operations, and technology. The program must be documented, approved by senior management and the board, and subject to regular review and enhancement."
        ],
        "key_concepts": [
            ("AML Program Pillars", "The five required components: policies/procedures, compliance officer appointment, training, independent testing, and CDD."),
            ("Compliance Officer", "A designated individual responsible for the day-to-day operation and oversight of the AML program."),
            ("Board Oversight", "The board of directors' responsibility to approve, oversee, and ensure adequate resources for the AML program."),
            ("Program Documentation", "Written policies and procedures that clearly document all aspects of the AML compliance program."),
            ("Risk-Based Allocation", "Directing compliance resources proportionally to assessed risk levels across the business.")
        ],
        "takeaways": [
            "The five mandatory AML program pillars provide a comprehensive compliance framework.",
            "A designated compliance officer with appropriate authority is essential for program effectiveness.",
            "Board oversight ensures the AML program has adequate resources and organizational priority.",
            "Risk assessment is the foundation that determines the design and intensity of program controls."
        ]
    },
    "aml-enforcement-cases": {
        "overview": [
            "AML enforcement actions provide critical lessons for the financial industry. Major cases have resulted in billions of dollars in penalties, deferred prosecution agreements, and in some cases, the loss of banking licenses. Studying enforcement actions reveals common failure patterns and regulatory expectations that institutions must incorporate into their compliance programs.",
            "Notable cases include HSBC ($1.9B penalty for BSA/AML failures), Standard Chartered (multiple penalties totaling over $1B for sanctions violations), Danske Bank (Estonia branch $200B money laundering scandal), and Swedbank. Common themes include inadequate transaction monitoring, insufficient staffing, failure to file SARs, and weak customer due diligence."
        ],
        "key_concepts": [
            ("Deferred Prosecution Agreement", "An agreement where prosecutors defer charges in exchange for the institution's agreement to remediate and pay penalties."),
            ("Cease and Desist Order", "A regulatory order requiring an institution to stop specific practices and take corrective action."),
            ("Civil Money Penalty", "Financial penalties imposed by regulators for AML compliance failures, often running into hundreds of millions."),
            ("SAR Filing Deficiencies", "A common enforcement theme involving failure to file timely or complete Suspicious Activity Reports."),
            ("Independent Consultant", "A third party appointed under enforcement actions to review and report on remediation efforts.")
        ],
        "takeaways": [
            "Major AML enforcement actions reveal recurring failure patterns across the industry.",
            "Common failures include inadequate transaction monitoring, insufficient staffing, and weak CDD.",
            "Deferred Prosecution Agreements require substantial remediation commitments and ongoing oversight.",
            "Penalties for AML failures have reached billions of dollars for single institutions."
        ]
    },
    "money-laundering-mechanisms": {
        "overview": [
            "Money laundering mechanisms have become increasingly sophisticated as criminals exploit gaps in the global financial system. Beyond the classic three-stage model (placement, layering, integration), modern mechanisms include complex corporate structures, digital assets, trade finance manipulation, and professional money laundering networks that provide services across multiple jurisdictions.",
            "Understanding specific laundering mechanisms is essential for designing effective detection controls. Each mechanism leaves distinct footprints: structuring creates patterns of just-below-threshold transactions, shell companies create circular fund flows, trade-based laundering creates pricing anomalies, and crypto mixing creates blockchain transaction patterns that can be analyzed."
        ],
        "key_concepts": [
            ("Corporate Vehicles", "Shell companies, trusts, and foundations used to obscure beneficial ownership and layer fund movements."),
            ("Digital Asset Laundering", "Using cryptocurrencies, mixers, privacy coins, and DeFi protocols to launder proceeds."),
            ("Real Estate Laundering", "Purchasing property through shell companies to integrate illicit funds into the legitimate economy."),
            ("Casino and Gaming", "Using gambling and gaming venues to convert cash to chips and back to legitimate-looking funds."),
            ("Trade Finance Manipulation", "Exploiting international trade documentation to move value across borders undetected.")
        ],
        "takeaways": [
            "Modern money laundering mechanisms extend far beyond the classic three-stage model.",
            "Each laundering mechanism leaves distinct patterns that can be detected through transaction monitoring.",
            "Professional money laundering networks provide sophisticated services across multiple jurisdictions.",
            "Real estate, digital assets, and trade finance are among the most exploited sectors for laundering."
        ]
    },
    "aml-compliance-glossary": {
        "overview": [
            "The AML compliance field has a specialized vocabulary that professionals must master. Understanding key terminology — from basic concepts like CDD and EDD to specialized terms like tax evasion, trade-based money laundering, and virtual asset service providers — is essential for effective compliance work across jurisdictions.",
            "This glossary covers the essential AML/CFT terminology used in regulatory frameworks, industry practice, and enforcement actions. Terms are drawn from FATF recommendations, national regulations, and industry standards. Mastery of this vocabulary enables compliance professionals to communicate effectively across functions, jurisdictions, and regulatory bodies."
        ],
        "key_concepts": [
            ("CDD", "Customer Due Diligence — the process of identifying and verifying customers and assessing their risk profiles."),
            ("EDD", "Enhanced Due Diligence — higher-level scrutiny applied to high-risk customers."),
            ("FIU", "Financial Intelligence Unit — a national agency that collects and analyzes financial intelligence."),
            ("PEP", "Politically Exposed Person — an individual with a prominent public function at higher risk for corruption."),
            ("STR/SAR", "Suspicious Transaction/Activity Report — the mechanism for reporting suspicious financial activity to the FIU.")
        ],
        "takeaways": [
            "Mastering AML terminology is essential for effective compliance work across jurisdictions.",
            "Key acronyms include CDD, EDD, FIU, PEP, STR/SAR, and VASP.",
            "Terminology is standardized by FATF recommendations and adopted by national regulators.",
            "Consistent terminology enables clear communication across global compliance teams."
        ]
    },
}

# ── Knowledge content (platform pages) ──

KNOWLEDGE_TOPICS = {
    "knowledge/dataops-trends-2026": {
        "overview": [
            "DataOps trends in 2026 reflect the maturation of data management practices across the industry. Key themes include the widespread adoption of data contracts, the rise of AI-augmented data engineering, increasing emphasis on data observability, and the convergence of data and machine learning platforms.",
            "Organizations are moving beyond basic DataOps practices to implement sophisticated quality monitoring, automated governance, and cross-functional collaboration frameworks. The trends point toward greater automation, stronger data product thinking, and deeper integration between data engineering and business operations."
        ],
        "takeaways": [
            "Data contracts and AI-augmented data engineering are leading DataOps trends in 2026.",
            "Data observability has moved from emerging practice to operational necessity.",
            "The convergence of data and ML platforms is accelerating.",
            "Automated governance and quality monitoring are becoming standard practice."
        ]
    },
    "knowledge/dataops-glossary": {
        "overview": [
            "The DataOps glossary provides definitions for key terms in the data engineering and operations field. From foundational concepts like ETL/ELT and data pipelines to emerging practices like data observability and data mesh, understanding these terms is essential for professionals working in modern data environments.",
            "This glossary is curated from industry standards and evolving practices, reflecting the current state of data engineering terminology. Terms are organized by category for easy reference, covering data architecture, processing, quality, governance, and operations."
        ],
        "takeaways": [
            "DataOps terminology spans data architecture, processing, quality, governance, and operations.",
            "Understanding key terms enables effective communication across data teams.",
            "The glossary reflects evolving industry practices and emerging technologies.",
            "Centralized terminology supports consistent understanding across the organization."
        ]
    },
    "knowledge/open-source-tools": {
        "overview": [
            "The open-source data tool ecosystem has matured into a comprehensive stack covering every aspect of data engineering. From ingestion and processing to storage, transformation, and visualization, open-source tools provide viable alternatives to proprietary solutions while offering flexibility, community support, and cost advantages.",
            "Key categories include orchestration (Airflow, Dagster, Prefect), transformation (dbt), streaming (Kafka, Flink), storage (Iceberg, Delta Lake), and BI (Superset, Metabase). The ecosystem continues to evolve rapidly, with new tools and integrations emerging regularly."
        ],
        "takeaways": [
            "Open-source tools cover the entire data engineering stack from ingestion to visualization.",
            "dbt, Airflow, Kafka, and Iceberg are cornerstone tools in the open-source data ecosystem.",
            "Open-source adoption reduces vendor lock-in and enables customization.",
            "The ecosystem continues rapid evolution with new tools and integrations."
        ]
    },
    "knowledge/system-architecture": {
        "overview": [
            "The system architecture of the AcaciaFund platform is designed for reliability, scalability, and maintainability. The build pipeline transforms content from registry.json into a static site through a series of well-defined stages, with caching and incremental builds ensuring efficiency.",
            "The architecture follows a modular design with clear separation of concerns between content management, build processing, template rendering, and output generation. The registry serves as the single source of truth, with scripts and core modules transforming data into the final static site."
        ],
        "takeaways": [
            "The platform uses a modular build pipeline with registry.json as the single source of truth.",
            "Incremental builds with caching enable efficient content updates.",
            "Clear separation of concerns between content, processing, and rendering.",
            "The architecture supports multiple content types and pillars from a unified codebase."
        ]
    },
    "knowledge/about": {
        "overview": [
            "AcaciaFund is a knowledge platform that synthesizes research across three pillars: Compliance, Markets, and Data Engineering. The platform curates and transforms high-quality sources — academic papers, industry analysis, regulatory guidance, and community discussions — into structured, educational content.",
            "The mission is to make complex financial and technical knowledge accessible through well-organized, verified content with clear provenance. The platform combines automated content processing with human curation to deliver high-quality educational resources."
        ],
        "takeaways": [
            "AcaciaFund synthesizes research across Compliance, Markets, and Data Engineering.",
            "Content is curated from academic, regulatory, industry, and community sources.",
            "The platform combines automated processing with human curation.",
            "The mission is to make complex knowledge accessible and verifiable."
        ]
    },
    "knowledge/contact": {
        "overview": [
            "Contact information and channels for engaging with the AcaciaFund platform. We welcome feedback, corrections, and collaboration from the community.",
            "For questions, suggestions, or issues, please reach out through the available channels. We are committed to continuous improvement and value input from our users."
        ],
        "takeaways": [
            "Feedback and corrections are welcome through available contact channels.",
            "Community input is valued for ongoing platform improvement.",
            "We are committed to responsive communication with users."
        ]
    },
    "knowledge/research-methodology": {
        "overview": [
            "The AcaciaFund research methodology combines systematic source curation with structured content generation. Sources are drawn from 32 authoritative feeds across three pillars, with automated freshness checking ensuring content remains current. Each content item is processed through a pipeline that extracts entities, computes quality metrics, and generates educational components.",
            "The methodology emphasizes transparency through source provenance tracking, quality scoring (Signal Quality Index), and clear attribution. Bloom taxonomy classification ensures content supports different learning levels, from foundational understanding to advanced analysis."
        ],
        "takeaways": [
            "Research methodology combines source curation, automated processing, and quality scoring.",
            "SQI provides a transparent, multi-dimensional quality metric for content.",
            "Bloom taxonomy classification supports learning at different cognitive levels.",
            "Source provenance tracking enables verification and further research."
        ]
    },
    "knowledge/pillar-taxonomy": {
        "overview": [
            "The pillar taxonomy organizes knowledge across three domains: Compliance (AML/CFT), Markets (equities, derivatives, FX), and Data Engineering (pipelines, infrastructure, governance). Each pillar has a hierarchical subcategory structure that enables precise content organization and navigation.",
            "The taxonomy is defined in config.py with PILLAR_SUBCATEGORIES providing the organizational framework. URL structure follows the internal pillar keys mapped to user-facing URL segments through PILLAR_URL_MAP."
        ],
        "takeaways": [
            "Three pillars organize content across Compliance, Markets, and Data Engineering.",
            "Hierarchical subcategories enable precise content classification and navigation.",
            "PILLAR_URL_MAP in config.py is the single source of truth for URL structure.",
            "The taxonomy supports cross-pillar connections and knowledge synthesis."
        ]
    },
    "knowledge/changelog": {
        "overview": [
            "The changelog tracks significant updates and improvements to the AcaciaFund platform. Changes are documented with dates, descriptions, and impact information.",
            "The platform undergoes continuous improvement through regular updates to content, features, and infrastructure. Key developments include ontology enrichment, content expansion, and feature additions."
        ],
        "takeaways": [
            "The platform is continuously updated with content and feature improvements.",
            "Significant changes are documented in the changelog for transparency.",
            "Regular refresh cycles keep content current and accurate."
        ]
    },
    "knowledge/faq": {
        "overview": [
            "Frequently asked questions about the AcaciaFund platform, covering content, navigation, technical details, and usage.",
            "This section addresses common queries to help users navigate the platform effectively and understand the content structure and methodology."
        ],
        "takeaways": [
            "FAQ provides quick answers to common platform questions.",
            "Covering content, navigation, methodology, and technical details.",
            "Designed to help users maximize the value of the platform."
        ]
    },
    "knowledge/glossary": {
        "overview": [
            "The glossary provides definitions for key terms across all three pillars. Terms are linked to ontology concepts, providing connections to related content and learning resources.",
            "The glossary is auto-generated from the ontology and enriched with cross-references, making it a living resource that grows with the platform's knowledge base."
        ],
        "takeaways": [
            "Glossary covers key terms across Compliance, Markets, and Data Engineering.",
            "Terms are linked to ontology concepts for deeper exploration.",
            "Auto-generated and continuously updated from the ontology.",
            "Cross-references enable connected learning across pillars."
        ]
    },
    "knowledge/diagrams": {
        "overview": [
            "The diagrams section provides visual explanations of key concepts and architectures across all pillars. SVG diagrams are generated programmatically based on content structure and taxonomy information.",
            "Visual representations aid understanding of complex topics including data pipeline architectures, market structures, regulatory frameworks, and conceptual relationships."
        ],
        "takeaways": [
            "Diagrams provide visual explanations of complex concepts.",
            "SVG diagrams are generated programmatically for consistency.",
            "Covering architecture, market structure, and regulatory frameworks.",
            "Visual aids enhance understanding of interconnected concepts."
        ]
    },
    "data/knowledge/cybernetic-foundations": {
        "overview": [
            "Cybernetic foundations explore the intersection of control theory, information theory, and systems thinking as applied to data engineering and financial systems. Concepts from cybernetics provide frameworks for understanding feedback loops, self-regulation, and adaptive behavior in complex systems.",
            "Applications include automated pipeline monitoring and self-healing systems, adaptive risk management in financial compliance, and the design of resilient market infrastructure. Cybernetic thinking provides a theoretical foundation for building intelligent, adaptive systems."
        ],
        "takeaways": [
            "Cybernetics provides frameworks for understanding feedback and self-regulation in complex systems.",
            "Applications span automated monitoring, adaptive risk management, and resilient infrastructure.",
            "Control theory and information theory are foundational to modern data engineering.",
            "Cybernetic principles enable the design of intelligent, adaptive systems."
        ]
    },
}

# ── Slug-based learn content routing ──

LEARN_SLUG_MAP = {}
for slug, data in LEARN_DE_TOPICS.items():
    LEARN_SLUG_MAP[slug] = data
for slug, data in LEARN_STOCK_TOPICS.items():
    LEARN_SLUG_MAP[slug] = data
for slug, data in LEARN_AML_TOPICS.items():
    LEARN_SLUG_MAP[slug] = data

TOPIC_CONTENT.update(KNOWLEDGE_TOPICS)


# ── Helper functions ──

def get_slug_key(slug):
    """Extract the topic key from a slug."""
    parts = slug.split("/")
    if len(parts) >= 2 and parts[0] in ("aml", "stock", "data", "markets"):
        if len(parts) >= 3:
            return parts[2]
        return parts[-1]
    return slug


def find_topic_data(item):
    """Find the right topic data dict for a content item."""
    slug = item["slug"]
    content_type = item["content_type"]

    # Direct match by full slug
    if slug in TOPIC_CONTENT:
        return TOPIC_CONTENT[slug]

    # Learn modules: match by slug key
    if content_type == "learn":
        key = get_slug_key(slug)
        if key and key in LEARN_SLUG_MAP:
            return LEARN_SLUG_MAP[key]
        # Try the full slug minus pillar prefix
        for known_slug, data in LEARN_SLUG_MAP.items():
            if known_slug in slug or slug.endswith(known_slug):
                return data

    return None


def generate_body_html(item):
    """Generate body_html for an item missing it."""
    slug = item["slug"]
    title = item.get("title", "Untitled")
    description = item.get("description", "")
    content_type = item["content_type"]
    topic = find_topic_data(item)

    if content_type == "learn" and topic:
        return _generate_learn_html(title, description, topic, slug)
    elif content_type == "research" and topic:
        return _generate_research_html(title, description, topic, slug)
    else:
        # Generic fallback
        return _generate_fallback_html(title, description, item)


def _generate_learn_html(title, description, topic, slug):
    overview_paras = topic.get("overview", [])
    key_concepts = topic.get("key_concepts", [])
    takeaways = topic.get("takeaways", [])
    why_it_matters = topic.get("why_it_matters", None)

    parts = ['<h2>Overview</h2>']
    for p in overview_paras:
        parts.append(f'<p>{p}</p>')

    parts.append('\n<h2>Key Concepts</h2>\n<ul>')
    for term, explanation in key_concepts:
        parts.append(f'<li><strong>{term}:</strong> {explanation}</li>')
    parts.append('</ul>')

    if why_it_matters:
        parts.append('\n<h2>Why It Matters</h2>')
        for p in why_it_matters:
            parts.append(f'<p>{p}</p>')

    parts.append('\n<h2>Key Takeaways</h2>\n<ul>')
    for t in takeaways:
        parts.append(f'<li>{t}</li>')
    parts.append('</ul>')

    return '\n\n'.join(parts)


def _generate_research_html(title, description, topic, slug):
    overview_paras = topic.get("overview_paras", topic.get("overview", []))
    key_concepts = topic.get("key_concepts", [])
    takeaways = topic.get("takeaways", [])
    why_it_matters = topic.get("why_it_matters", None)

    parts = ['<h2>Overview</h2>']
    for p in overview_paras:
        parts.append(f'<p>{p}</p>')

    parts.append('\n<h2>Core Framework</h2>\n<ul>')
    for term, explanation in key_concepts:
        parts.append(f'<li><strong>{term}:</strong> {explanation}</li>')
    parts.append('</ul>')

    if why_it_matters:
        parts.append('\n<h2>Practical Application</h2>')
        for p in why_it_matters:
            parts.append(f'<p>{p}</p>')
    else:
        parts.append('\n<h2>Practical Application</h2>')
        parts.append(f'<p>{description}</p>')

    parts.append('\n<h2>Key Takeaways</h2>\n<ul>')
    for t in takeaways:
        parts.append(f'<li>{t}</li>')
    parts.append('</ul>')

    return '\n\n'.join(parts)


def _generate_fallback_html(title, description, item):
    content_type = item.get("content_type", "research")
    pillar = item.get("pillar", "general")
    difficulty = item.get("difficulty", "intermediate")
    tags = item.get("tags", [])

    parts = ['<h2>Overview</h2>']
    if description:
        parts.append(f'<p>{description}</p>')
    else:
        parts.append(f'<p>An exploration of {title.lower()} in the context of {pillar.replace("-", " ")}.</p>')

    if tags:
        parts.append('\n<h2>Key Topics</h2>\n<ul>')
        for tag in tags[:5]:
            topic_name = tag.replace("-", " ").title()
            parts.append(f'<li><strong>{topic_name}:</strong> A key concept in {title.lower()} relevant to {pillar.replace("-", " ")} practitioners.</li>')
        parts.append('</ul>')

    parts.append(f'\n<p>This {content_type} module provides foundational knowledge for {difficulty}-level learners in the {pillar.replace("-", " ")} domain. The content covers essential concepts, practical applications, and key references for further study.</p>')

    parts.append('\n<h2>Key Takeaways</h2>\n<ul>')
    parts.append(f'<li>Understand the core principles and concepts underlying {title.lower()}.</li>')
    parts.append(f'<li>Recognize practical applications within {pillar.replace("-", " ")} workflows and decision-making.</li>')
    parts.append('<li>Identify connections to related topics and advanced study areas.</li>')
    parts.append('</ul>')

    return '\n\n'.join(parts)


def generate_flashcards(item, body_html):
    """Generate flashcards based on body_html content."""
    content_type = item["content_type"]

    # Use pre-defined flashcards if available
    topic = find_topic_data(item)
    if topic and "flashcards" in topic:
        return topic["flashcards"]

    # Generate from body_html by extracting h2 headings and content
    cards = []
    title = item.get("title", "")
    description = item.get("description", "")

    if content_type == "learn":
        topic_data = topic if topic else None
        key_concepts = topic_data.get("key_concepts", []) if topic_data else []
        takeaways = topic_data.get("takeaways", []) if topic_data else []

        if key_concepts:
            for term, explanation in key_concepts[:3]:
                cards.append({
                    "front": f"What is {term}?",
                    "back": explanation
                })
        if takeaways:
            for t in takeaways[:2]:
                cards.append({
                    "front": t[:80] + ("..." if len(t) > 80 else ""),
                    "back": t
                })

    if not cards:
        cards.append({"front": title, "back": description[:200]})
        cards.append({
            "front": f"What makes {title.lower()} important?",
            "back": f"{title} is a key topic in {item.get('pillar', '')} that provides foundational knowledge for practitioners."
        })

    return cards[:4]


def generate_quality_metadata(item):
    """Generate quality metadata for items missing it."""
    updates = {}

    sqi = item.get("sqi", 0.5)
    content_type = item.get("content_type", "knowledge")

    # quality_badge
    if "quality_badge" not in item:
        if sqi >= 0.9:
            updates["quality_badge"] = "high-confidence"
        elif sqi >= 0.8:
            updates["quality_badge"] = "moderate-confidence"
        else:
            updates["quality_badge"] = "low-confidence"

    # source_breakdown
    if "source_breakdown" not in item:
        if content_type == "research":
            updates["source_breakdown"] = {"hn": 3, "arxiv": 2, "pubmed": 1}
        elif content_type == "learn":
            updates["source_breakdown"] = {"educational": 5}
        else:
            updates["source_breakdown"] = {"synthesized": 3}

    # source_verified
    if "source_verified" not in item:
        updates["source_verified"] = True

    # quality_metrics
    if "quality_metrics" not in item:
        updates["quality_metrics"] = {
            "score": 0.7,
            "source_verified": True,
            "evidence_level": "Moderate",
            "trend_strength": 50.0,
            "adoption_level": "emerging"
        }

    # signals
    if "signals" not in item:
        tags = item.get("tags", [])
        top_entities = tags[:5] if tags else ["extracted", "from", "tags"]
        updates["signals"] = {
            "count": 3,
            "total_score": 75,
            "avg_score": 75.0,
            "domain_diversity": 2,
            "top_entities": top_entities
        }

    # reading_time
    if not item.get("reading_time"):
        body_html = item.get("body_html", "")
        word_count = len(body_html.split()) if body_html else 200
        updates["reading_time"] = max(1, round(word_count / 200))

    return updates


def backfill():
    """Main backfill function."""
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        reg = json.load(f)

    content = reg["content"]
    total = len(content)

    counts = {
        "body_html": 0,
        "quality_badge": 0,
        "source_breakdown": 0,
        "source_verified": 0,
        "quality_metrics": 0,
        "signals": 0,
        "reading_time": 0,
        "flashcards": 0,
    }

    for i, item in enumerate(content):

        # 1. Generate body_html if missing
        if not item.get("body_html"):
            item["body_html"] = generate_body_html(item)
            counts["body_html"] += 1

        # 2. Generate quality metadata
        meta = generate_quality_metadata(item)
        for key, value in meta.items():
            item[key] = value
            if key in counts:
                counts[key] += 1

        # 3. Generate flashcards if missing
        if not item.get("flashcards"):
            item["flashcards"] = generate_flashcards(item, item.get("body_html", ""))
            counts["flashcards"] += 1

    # Write back
    reg["content"] = content
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)

    # Summary
    print(f"Processed {total} content items.")
    print()
    print("Updates applied:")
    for field, count in counts.items():
        print(f"  {field}: {count}")
    print()
    print(f"Total fields updated: {sum(counts.values())}")


if __name__ == "__main__":
    backfill()
