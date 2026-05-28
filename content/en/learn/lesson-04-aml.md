---
title: "Lesson 4 — AML: Risk Assessment and Regulatory Decisions"
date: 2026-05-28
type: "lesson"
difficulty: "medium"
tags: ["aml","judgment","regulation","risk"]
tldr: "In AML, key is recognizing patterns of suspicious activity and making decisions based on incomplete information."
takeaways: 
  - "Distinguishing between legal and suspicious behavior requires analyzing context and behaviors."
  - "Regulatory decisions often rely on probability, not certainty."
  - "Applying Bayesian principles helps update beliefs about risk based on new evidence."
---

![AML illustration](/images/aml-thumb.svg)

## Introduction

In the fight against money laundering and terrorist financing, financial institutions and regulatory bodies must make decisions under uncertainty. We don't have a full picture of a customer's activities, but we must assess risk based on available signals (transactions, behaviors, profiles).

### Why is AML risk assessment a matter of judgment?

- We cannot rely solely on rules (e.g., "transaction over EUR 10,000") because criminals adapt their behavior.
- We must combine many weak signals into a single risk assessment.
- The decision to block a transaction or report it to authorities has business and legal consequences.

### Example from the portal: Spain blocks prediction markets

In the recent AML synthesis (2026-05-27), we saw that Spain deemed platforms like Polymarket and Kalshi to violate gambling regulations, despite presenting themselves as prediction markets. This decision required:
- Analyzing the platform's intent (is it mainly for gambling or forecasting?)
- Assessing legal and reputational risk
- Considering the impact on fintech innovation

## How to think like an AML investigator?

### Step 1: Gather signals
Instead of looking for one "smoking gun," gather multiple clues:
- Unusual transaction patterns (structuring, rapid turnover)
- Inconsistencies in customer information
- Links to high-risk entities
- Behaviors suggesting evasion of detection

### Step 2: Assess probability
Use Bayesian thinking:
- Start with an initial risk assessment (e.g., based on customer profile)
- Update it with each new signal
- The more atypical the signal, the greater the impact on the update

### Step 3: Make decisions under uncertainty
Don't wait for 100% certainty (which is often unavailable). Instead:
- Set an action threshold (e.g., when risk probability exceeds 70%)
- Consider the costs of Type I (false positive) vs Type II (false negative) errors
- Remember the alert fatigue effect: overly strict thresholds generate many false alarms, costing time and customer trust.

## Quiz

Test your understanding of AML risk assessment principles.

<div class="quiz" data-quiz='{"questions":[{"q":"Which of the following is the best example of a signal requiring further analysis in AML?","options":["Customer makes a one-time large transaction reported as savings","Customer makes many small transactions below reporting threshold in short time","Customer regularly receives salary from their employer"],"a":1},{"q":"Why must the decision to block a transaction in AML often be made before full evidence is collected?","options":["Because criminals quickly move funds","Because banks lack access to full customer data","Because law requires immediate action"],"a":0},{"q":"How does Bayesian thinking help in AML?","options":["Guarantees detection of all money laundering cases","Allows updating risk assessment based on new evidence","Replaces human analysts with algorithms"],"a":1}]}'></div>

## Summary

AML risk assessment is not a checklist compliance exercise but a continuous process of updating beliefs based on incomplete information. Developing judgment in this area not only makes you a better analyst but also teaches one of the most important skills of the modern world: making decisions under uncertainty.

---