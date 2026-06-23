---
schema: gitops
change-type: modificative
blast-radius: medium
slo-impact: <0.01%
change-window: scheduled
author: jane-sre
date: 2024-03-18
---

# GitOps Proposal: Migrate frontend-apps ApplicationSet to cluster generator

## Problem

The `frontend-apps` ApplicationSet uses a `list` generator with hardcoded cluster entries. Adding a new cluster requires manually editing the ApplicationSet, which is error-prone. During the v2.4.0 rollout (INC-2024-089), the `prod-eu-west-1` cluster was forgotten and received the update 45 minutes after all other clusters.

## Motivation

The platform team adds approximately one cluster per quarter. Each addition requires a manual edit to `frontend-apps` ApplicationSet, and any missed update causes deployment inconsistency across clusters. INC-2024-089 caused 45 minutes of degraded deployment coverage in EU.

## Proposed solution

Migrate the `frontend-apps` ApplicationSet generator from `list` (hardcoded clusters) to `cluster` (dynamic selection by label `platform/frontend: "true"`). New clusters will be automatically included when labeled, eliminating manual ApplicationSet updates.

## Alternatives considered

| Alternative | Reason discarded |
|-------------|-----------------|
| Keep `list` generator, add CI check for cluster list | Doesn't fix root cause; adds CI complexity |
| Use `git` generator with a clusters inventory file | Two places to update when adding a cluster |

## Expected outcome

- Eliminate manual ApplicationSet updates when adding new clusters
- Reduce cluster onboarding time from ~2h (manual + review) to ~10min (label only)
- Prevent class of incidents caused by missed cluster in ApplicationSet

## Required approvals

| Role | Name | Status |
|------|------|--------|
| SRE Lead | @maria-sre | ✅ Approved 2024-03-17 |
| Platform Engineer owner | @john-platform | ✅ Approved 2024-03-17 |

## Dependencies

- [x] All 3 clusters have label `platform/frontend: "true"` configured

## Related links

- Incident: INC-2024-089
- ArgoCD docs: cluster generator
