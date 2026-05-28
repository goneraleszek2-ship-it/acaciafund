---
title: "Lesson 3 — Privacy & Aggregation"
date: 2026-05-22
type: "lesson"
difficulty: "medium"
tags: ["privacy","dp"]
tldr: "Differential privacy adds noise to protect individual data while allowing useful aggregate analysis. ε (epsilon) is the privacy budget - lower means more privacy."
takeaways: 
  - "Differential privacy guarantees that removing or changing one record doesn't significantly affect outcomes"
  - "The privacy budget ε controls the trade-off between privacy and accuracy"
  - "Acacia uses differential privacy to protect contributors while providing useful aggregates"
---
![Privacy illustration](/images/privacy.svg)

## Introduction

In the era of big data, protecting individual privacy while still deriving valuable statistical analyses is crucial. Differential privacy (DP) is a mathematical framework that enables both: protection of individual data and obtaining useful aggregate results.

### Why traditional approaches fail?

Simple removal of identifying information (anonymization) often proves insufficient. For example, knowing ZIP code, birth date, and gender can identify a significant portion of the population. Moreover, even if data are aggregated, sometimes one can infer about individuals through attacks like "differencing" or "reconstruction".

### How does differential privacy work?

The core idea is to add carefully calibrated noise to the outputs of statistical queries (e.g., counts, averages). The noise is calibrated such that:
- The probability of obtaining any particular outcome practically does not change whether a specific individual's data is in the database or not.
- Simultaneously, if the query concerns a large group, the added noise is relatively small compared to the true value, so the result remains useful.

Formally, a mechanism 𝓜 provides ε-differential privacy if for all pairs of databases D and D' differing in at most one record, and for all possible outputs S:
$$
Pr[\mathcal{M}(D) \in S] \leq e^\varepsilon \cdot Pr[\mathcal{M}(D') \in S]
$$
The smaller ε, the stronger the privacy guarantee (less influence of changing one record).

### Choice of noise

Commonly used mechanisms include:
- **Laplace mechanism** – adds Laplace-distributed noise with scale proportional to the query sensitivity (e.g., for a count, sensitivity is 1).
- **Gaussian mechanism** – adds normally distributed noise, used when (ε,δ)-differential privacy is required (allows some flexibility while preserving utility).
- **Exponential mechanism** – used for selecting from categories (e.g., choosing the most frequent answer).

### Example: Counting individuals with a property

Suppose we want to count how many individuals in a database smoke cigarettes, while preserving each respondent's privacy.
- True count: 150 persons.
- Sensitivity of the query (changing one record can change the count by at most 1): Δ = 1.
- We add Laplace noise with scale Δ/ε. At ε = 1, scale = 1.
- The result might look like 149.3 or 152.7 – we do not learn the exact count, but the error is usually small relative to the group size.

### Applications in Acacia

In the Acacia project, we use differential privacy to:
1. **Aggregate opinions** – when many users rate the same article or idea, we add noise to the average rating to prevent reading individual votes.
2. **Publish topic statistics** – the number of occurrences of specific tags (e.g., "AML", "bayes") is published with added noise, so one cannot infer whether a particular user added or removed a given tag.
3. **Time‑series trend analysis** – we track how interest in a topic changes week by week, while protecting the privacy of individuals responsible for the individual posts.

### The privacy–utility trade‑off

The key parameter is ε (epsilon):
- **Small ε** (e.g., 0.1) → very strong privacy, but results may be very noisy and useless for small groups.
- **Large ε** (e.g., 5.0) → weaker privacy guarantee, but results closer to true values.
In practice, ε is chosen depending on context: for highly sensitive data one uses smaller ε, for public statistics one can allow larger ε.

### Reflection

Consider what kinds of data you would be willing to share in aggregate form, and what you consider too sensitive even after adding noise. Are there situations where you would prefer to completely forgo sharing data, even if it means losing certain insights?

### Quiz

<div class="quiz" data-quiz='{"questions":[{"q":"What does differential privacy guarantee?","options":["Full anonymization of data","That changing one record does not significantly affect the query result","That data are encrypted with a public key"],"a":1},{"q":"How does ε (epsilon) affect differential privacy?","options":["The larger ε, the stronger the privacy","The smaller ε, the stronger the privacy","ε has no effect on the privacy level"],"a":1},{"q":"Which mechanism is often used to publish average values while preserving differential privacy?","options":["Exponential mechanism","Laplace or Gaussian mechanism","Permutation mechanism"],"a":1}]}'></div>