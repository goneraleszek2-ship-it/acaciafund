---
title: "Learning Ecosystem Demo"
date: 2026-05-22
type: "page"
draft: false
---

## Core Mathematical Ideals

Below are the primary mathematical principles that power the Acacia learning ecosystem.

<div class="pictogram-grid" style="display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start;">
  <figure style="width:220px;text-align:left;">
    <img src="/images/bayes.svg" alt="Bayesian reasoning" style="width:160px;height:auto;"/>
    <figcaption style="font-family:Inter,Arial;font-size:13px;color:#111;margin-top:6px;">Bayesian Reasoning</figcaption>
  </figure>
  <figure style="width:220px;text-align:left;">
    <img src="/images/dp.svg" alt="Differential privacy" style="width:160px;height:auto;"/>
    <figcaption style="font-family:Inter,Arial;font-size:13px;color:#111;margin-top:6px;">Differential Privacy</figcaption>
  </figure>
  <figure style="width:220px;text-align:left;">
    <img src="/images/crypto.svg" alt="Cryptography" style="width:160px;height:auto;"/>
    <figcaption style="font-family:Inter,Arial;font-size:13px;color:#111;margin-top:6px;">Cryptography & Signatures</figcaption>
  </figure>
  <figure style="width:260px;text-align:left;">
    <img src="/images/mosa.svg" alt="MOSA modular" style="width:240px;height:auto;"/>
    <figcaption style="font-family:Inter,Arial;font-size:13px;color:#111;margin-top:6px;">MOSA — Modular Graph</figcaption>
  </figure>
</div>

## Software Stack

The concentric diagram below shows the main software layers and example tools.

{{< figure src="/images/stack.svg" alt="Software stack" >}}

## Learning Hub

Browse lessons and mark progress. Click a lesson to open it and complete quizzes.

<div style="display:flex;gap:16px;flex-wrap:wrap;">
  {{ range where .Site.RegularPages "Section" "learn" }}
    <div>{{ partial "lesson-card.html" . }}</div>
  {{ end }}
</div>

## Interactive Bayesian Demo

Adjust prior belief and likelihood to see the posterior update.
{{< bayes prior="0.5" like="0.5" >}}
