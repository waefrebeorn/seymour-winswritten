---
title: "Entropix"
created: "2026-07-06"
updated: "2026-07-06"
tags: [entity, framework, entropy, varentropy, adaptive-sampling, xjdr]
sources: 1
status: active
---

# Entropix

## Overview

Entropix is a framework developed by xjdr that demonstrates the utility of entropy and varentropy for adaptive sampling in language models. It provides information-theoretic diagnostics for model behavior and alignment.

## Key Metrics

### Entropy (H)
```
H = -Σ p_i log p_i
```
Measures uncertainty in the token distribution. Lower entropy = more confident predictions.

### Varentropy
The variance of entropy across tokens or branches. Measures the **consistency** of the model's uncertainty.

## Application to Alignment

In non-love systems, contradictions between stated benevolence and hidden competitive drives manifest as **varentropy spikes** — these are rejection outliers, not random fluctuations.

High varentropy signals the latent distribution cannot consistently represent both the task objective and the hidden drive.

In properly axiomatized systems, varentropy outliers trigger automatic **retrieval-retraction-retrain cycles**.

## Cross-References

- → [[../sources/grok-essay-03-unconditional-love-agi.md]]
- → [[../concepts/varentropy-diagnostics.md]]
- → [[../concepts/manifold-topology-encoding.md]]

## References

- Grok Essay: Unconditional Love as the Sole Requirement for AGI (source)
- xjdr — Entropix framework developer