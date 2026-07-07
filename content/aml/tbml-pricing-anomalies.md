---
title: "Trade-Based Money Laundering (TBML) Detection via Statistical Pricing Anomaly Isolation"
slug: "tbml-pricing-anomalies"
pillar: "aml"
quality_score: 1.0
content_type: "deep-domain"
tags: ["aml", "statistical-modeling", "fraud-detection", "hawkes-microstructure"]
cross_vectors: ["hawkes-microstructure"]
---

# Trade-Based Money Laundering (TBML) Detection

## 1. Mechanics of Mis-Invoicing Vectors
Trade-Based Money Laundering (TBML) represents one of the most sophisticated methodologies for transferring value across international borders under the guise of legitimate commercial transactions. The primary operational vectors include:
* **Over-Invoicing:** The seller bills the buyer at a price significantly above market value, moving capital from the buyer's jurisdiction to the seller's.
* **Under-Invoicing:** The seller bills the buyer at a price significantly below market value, allowing the buyer to realize an outsized profit upon local resale.

To automate the detection of these fraudulent value transfers, transaction monitoring engines must cross-reference unit prices declared on customs manifests against high-frequency global spot market pricing distributions.

## 2. Mathematical Isolation via Z-Score and Interquartile Range (IQR) Profiles
Let $x_{c,t}$ be the declared unit price of a specific commodity code $c$ at transaction time $t$. We establish a dynamic reference distribution using historical global customs indices over an evaluation window $\Delta t$. The pricing variance is monitored using a dual-metric filtering framework:

$$\text{Z-Score}(x_{c,t}) = \frac{x_{c,t} - \mu_c}{\sigma_c}$$

Where $\mu_c$ is the running mean and $\sigma_c$ is the standard deviation of the global pricing matrix. To handle heavy-tailed or non-Gaussian commodity distributions, we supplement the Z-score check with a non-parametric Interquartile Range (IQR) fence:

$$\text{Lower Fence} = Q_1 - 1.5 \times \text{IQR}, \quad \text{Upper Fence} = Q_3 + 1.5 \times \text{IQR}$$

If $x_{c,t}$ violates the upper or lower fence constraints while simultaneously matching high-risk routing tags or shell company flags, the transaction entry is dynamically routed into an accelerated manual remediation queue.