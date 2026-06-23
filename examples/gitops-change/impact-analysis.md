---
schema: gitops
change-type: modificative
blast-radius: medium
slo-impact: <0.01%
change-window: scheduled
author: jane-sre
date: 2024-03-18
---

# GitOps Impact Analysis: Migrate frontend-apps ApplicationSet to cluster generator

## 1. Change scope

### 1.1 Affected clusters

| Cluster | Environment | Region | Impact |
|---------|-------------|--------|--------|
| `prod-us-east-1` | production | us-east-1 | modificative |
| `prod-eu-west-1` | production | eu-west-1 | modificative |
| `staging-us-east-1` | staging | us-east-1 | modificative |

**Total affected clusters**: 3

### 1.2 Modified ApplicationSets

| ApplicationSet | Namespace | Change type | Current generated Apps |
|----------------|-----------|-------------|------------------------|
| `frontend-apps` | `argocd` | modificative | 3 Applications |

### 1.3 Affected Applications

| Application | Target cluster | Target namespace | Affected? |
|-------------|----------------|------------------|-----------|
| `frontend-prod-us-east-1` | prod-us-east-1 | frontend | Yes — regenerated |
| `frontend-prod-eu-west-1` | prod-eu-west-1 | frontend | Yes — regenerated |
| `frontend-staging-us-east-1` | staging-us-east-1 | frontend | Yes — regenerated |

## 2. Change type

**Type**: `modificative`

The existing `frontend-apps` ApplicationSet will have its generator changed from `list` to `cluster`. Generated Applications will continue with the same sync configuration. A brief re-sync cycle is expected during apply.

**Is it additive?** No — modifies an existing ApplicationSet.
**Removes existing resources?** No — generated Applications remain.
**Affects `prune`?** No — prune configuration is unchanged (`prune: false`).

## 3. Blast radius

**Classified as**: `medium`

**Failure scenario: generator returns no clusters**
- Symptom: ApplicationSet generates 0 Applications
- Impact: All 3 clusters lose frontend Applications
- Detection: < 2 minutes (ArgoCD reconciliation loop)
- Recovery: < 5 minutes (git revert + ArgoCD auto-sync)

**Why not `high`?** Change does not affect syncPolicy or enable prune. Rollback is a git revert that takes under 5 minutes.

## 4. SLO impact

**Classified as**: `<0.01%`

| SLO | Target | Monthly budget | Change impact |
|-----|--------|----------------|---------------|
| Frontend Availability | 99.9% | 43.8 min | ~2 min (failure scenario) |

**Calculation**: 2 min / 43,800 min (monthly uptime) = 0.0046% of monthly uptime.

## 5. Change window

**Type**: `scheduled`

Tuesday–Thursday, 10:00–16:00 BRT. Duration: 30 minutes.
On-call notified in `#oncall-sre` before starting.

## 6. Prerequisites

- [x] Label `platform/frontend: "true"` confirmed on all 3 cluster Secrets
- [x] ArgoCD version >= 2.8 confirmed

## 7. Rollback triggers

Execute rollback immediately if:
- Generated Applications count drops below 3 for more than 2 minutes
- Any Application transitions from `Synced` to `Degraded`
- Frontend error rate exceeds 1% for 1 consecutive minute
