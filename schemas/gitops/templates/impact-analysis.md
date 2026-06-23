---
schema: gitops
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# GitOps Impact Analysis: [change title]

<!-- PSPEC:REQUIRED This document is a mandatory prerequisite before the technical design. All sections marked REQUIRED must be filled with real data, not vague estimates. -->

## 1. Change scope

### 1.1 Affected clusters

<!-- PSPEC:REQUIRED List ALL clusters that will be affected by the change. Include environment and region. -->

| Cluster | Environment | Region | Impact |
|---------|-------------|--------|--------|
| `prod-us-east-1` | production | us-east-1 | modificative |
| `prod-eu-west-1` | production | eu-west-1 | modificative |
| `staging-us-east-1` | staging | us-east-1 | modificative |

**Total clusters affected**: `3`

### 1.2 Modified ApplicationSets

<!-- PSPEC:REQUIRED List each ApplicationSet that will be created, modified, or deleted. -->

| ApplicationSet | Namespace | Change type | Current generated Applications |
|----------------|-----------|------------|--------------------------------|
| `frontend-apps` | `argocd` | modificative | 6 Applications |

### 1.3 Affected Applications

<!-- PSPEC:REQUIRED List the Applications that will be directly affected or regenerated. -->

| Application | Destination cluster | Destination namespace | Affected? |
|-------------|--------------------|-----------------------|-----------|
| `frontend-prod-us-east-1` | prod-us-east-1 | frontend | Yes — regenerated |
| `frontend-prod-eu-west-1` | prod-eu-west-1 | frontend | Yes — regenerated |
| `frontend-staging` | staging-us-east-1 | frontend | Yes — regenerated |

## 2. Change type

<!-- PSPEC:REQUIRED Select and justify the type. -->

**Type**: `modificative`

**Justification**: The existing `frontend-apps` ApplicationSet will have its generator changed from `list` to `cluster`. The generated Applications will continue to exist with the same sync configuration, but will go through a re-sync cycle during the apply.

**Is it additive?** No — modifies an existing ApplicationSet.
**Does it remove existing resources?** No — the generated Applications remain, only managed by the new generator.
**Does it affect `prune`?** No — the prune configuration remains unchanged.

## 3. Blast radius

<!-- PSPEC:REQUIRED Assess the blast radius in a partial or total failure scenario. -->

**Blast radius classified as**: `medium`

### 3.1 Failure scenario: generator returns no clusters

**Symptom**: ApplicationSet with `cluster` generator finds no clusters with the correct label.
**Impact**: ApplicationSet generates 0 Applications. Existing Applications are deleted if `prune: true`.
**Affected services**: Frontend in all environments (`3 clusters`)
**Estimated detection time**: < 2 minutes (ArgoCD reconciliation loop)
**Recovery time with rollback**: < 5 minutes (revert commit in the GitOps repo)

### 3.2 Failure scenario: incorrect labels on some clusters

**Symptom**: Only a subset of clusters appears in the generator.
**Impact**: Partial — some environments lose Applications, others continue normally.
**Affected services**: Frontend on clusters without the correct label.
**Mitigation**: PRE-APPLY verifies labels on all clusters before the apply.

### 3.3 Why not `high` or `critical`?

The change does not affect `syncPolicy` and does not activate `prune`. In case of generator failure, rollback is a commit revert and takes less than 5 minutes. No persisted data is affected.

## 4. SLO impact

<!-- PSPEC:REQUIRED Calculate the potential impact on the error budget. Read context/slo-budget.md for the calculation methodology. -->

**SLO impact classified as**: `<0.01%`

| SLO | Current target | Remaining monthly error budget | Impact of this change |
|-----|----------------|-------------------------------|----------------------|
| Frontend Availability | 99.9% | 43 min | ~2 min (failure scenario) |
| Frontend Latency p99 | 200ms | N/A — non-depleting | None |

**Calculation**: In a total failure scenario, recovery in < 5 minutes. 5 min / 43.8 min (monthly error budget) = ~11% of the remaining monthly budget. With current error budget of 43 min (budget intact), impact is 5/43820 ≈ 0.01% of monthly uptime.

**Requires budget approval?** No (approval threshold: >0.1%)

## 5. Change window

<!-- PSPEC:REQUIRED Determine if a formal change window is required. -->

**Change window**: `scheduled`

**Justification**: Medium blast radius + production impact requires a scheduled window, but does not require an incident commander. Apply outside peak hours.

**Recommended window**: Tuesday through Thursday, 10am–4pm EST (outside peak usage 7am–9am and 6pm–9pm)
**Estimated duration**: 30 minutes (15 min apply + 15 min validation)
**On-call notified?** Yes — notify the `#oncall-sre` channel before starting

## 6. Dependencies and prerequisites

<!-- PSPEC:REQUIRED List all dependencies that must exist BEFORE the apply. -->

- [ ] **Cluster labels**: All 3 clusters must have the label `platform/frontend: "true"` configured
  - Verification: `kubectl get clusters -l platform/frontend=true --all-namespaces`
  - Owner: @platform-sre
  - Deadline: before the change window

- [ ] **ArgoCD version**: ArgoCD >= 2.8 (support for `cluster` generator with compound label selectors)
  - Verification: `argocd version`
  - Current: verify before apply

## 7. Communication plan

<!-- PSPEC:OPTIONAL Define communication with stakeholders for medium blast radius or higher. -->

| Stakeholder | Channel | When | Message |
|-------------|---------|------|---------|
| Frontend team | `#frontend-eng` | 30 min before | "Planned maintenance on ArgoCD frontend-apps ApplicationSet" |
| On-call SRE | `#oncall-sre` | Immediately before | "Starting GitOps change window - frontend-apps" |
| SRE Lead | Direct | After completion | Change outcome |

## 8. Rollback trigger

<!-- PSPEC:REQUIRED Define objective criteria that trigger immediate rollback, without deliberation. -->

Execute immediate rollback if any condition occurs:

- ApplicationSet `frontend-apps` enters `Degraded` state for more than 2 minutes
- Number of generated Applications drops below 3 (expected: minimum 3)
- Any existing Application changes from `Synced` to `OutOfSync` without explanation
- Frontend error rate exceeds 1% for 1 consecutive minute
- Estimated time to recovery exceeds 10 minutes

**Rollback procedure**: see `runbook.md` section ROLLBACK
