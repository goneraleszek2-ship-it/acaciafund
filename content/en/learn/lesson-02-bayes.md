---
title: "Lesson 2 — Bayesian Thinking"
date: 2026-05-23
type: "lesson"
difficulty: "medium"
tags: ["bayes","probability","decision-making"]
tldr: "Bayesian thinking updates beliefs with new evidence using prior probabilities and likelihoods to form posterior probabilities."
takeaways: 
  - "Start with prior beliefs based on existing knowledge"
  - "Update beliefs when new evidence arrives using Bayes' theorem"
  - "Focus on likelihood ratios, not just raw probabilities"
---
![Bayesian illustration](/images/bayes.svg)

## Introduction

Bayesian thinking is a framework for updating our beliefs in light of new evidence. Instead of clinging rigidly to one hypothesis, we treat our beliefs as probabilities that can be changed depending on what we observe.

### Why is Bayesian thinking useful?

- It helps avoid errors from ignoring base rates (base rate neglect).
- It helps distinguish between the strength of evidence and its rarity.
- It enables quantitative combination of different sources of information.
- It is the foundation of many modern machine learning and artificial intelligence methods.

### Formalism: Bayes' Theorem

Bayes' Theorem describes how to update the probability of a hypothesis H given observation of evidence E:

$$
P(H|E) = \frac{P(E|H) \cdot P(H)}{P(E)}
$$

Where:
- $P(H)$ is the prior probability of the hypothesis (our initial belief).
- $P(E|H)$ is the probability of observing evidence E assuming hypothesis H is true (likelihood).
- $P(E)$ is the total probability of the evidence (normalizing factor).
- $P(H|E)$ is the posterior probability (updated belief after seeing the evidence).

Often it is more practical to focus on the odds ratio:

$$
\frac{P(H|E)}{P(\neg H|E)} = \frac{P(E|H)}{P(E|\neg H)} \cdot \frac{P(H)}{P(\neg H)}
$$

The posterior odds equal the prior odds multiplied by the likelihood ratio.

## Example: Disease Test

Imagine a test for a certain disease has:
- Sensitivity (probability of positive test given disease) = 99%
- Specificity (probability of negative test given no disease) = 95%
- Disease prevalence in the population (prior probability) = 0.1%

What is the probability that a person has the disease after receiving a positive test result?

Using Bayes' Theorem:
- $P(H) = 0.001$
- $P(E|H) = 0.99$
- $P(E|\neg H) = 1 - 0.95 = 0.05$ (false positive rate)
- $P(E) = P(E|H)P(H) + P(E|\neg H)P(\neg H) = 0.99*0.001 + 0.05*0.999 ≈ 0.05094$
- $P(H|E) = (0.99 * 0.001) / 0.05094 ≈ 0.0194$ → only about 1.94%

Even though the test is very accurate, due to the rarity of the disease most positive results are false alarms.

This example shows why it is important to take the prior probability into account.

{{< bayes prior="0.001" like="0.99" >}}

### Applications in Practice

1. **Medical diagnosis** – as above, combining test results with knowledge of disease prevalence.
2. **Spam filtering** – assessing the probability that a message is spam based on the words it contains.
3. **Credit risk evaluation** – updating the probability of default based on payment history and other indicators.
4. **Science and experiments** – updating beliefs about a scientific hypothesis in light of new experimental data.

### How to Practice Bayesian Thinking?

- Ask yourself: "What was my prior belief before seeing this evidence?"
- Assess how strong the evidence is: is it equally likely under different hypotheses?
- Update beliefs step by step as more evidence arrives.
- Use Bayes calculators or simple spreadsheets to compute posterior probabilities.
- Recognize situations where neglecting the base rate leads to erroneous conclusions.

### Reflection

Think about a recent situation where you changed your mind based on new information. Did you explicitly consider your prior belief? How strong was the evidence? Could you have quantified your update better?

### Quiz

<div class="quiz" data-quiz='{"questions":[{"q":"In the disease test example, why does a positive result still not mean a high probability of having the disease?","options":["Because the test is unreliable","Because the disease is very rare (low base rate)","Because doctors often make mistakes"],"a":1},{"q":"What is the likelihood ratio?","options":["The ratio of posterior to prior probability","The ratio of the probability of evidence under two different hypotheses","The ratio of true positives to false positives"],"a":1},{"q":"Which of the following practices helps avoid the base rate neglect error?","options":["Ignoring the frequency of the event in the population","Always starting with a 50/50 belief","Explicitly taking the base rate into account when evaluating evidence"],"a":2}]}'></div>