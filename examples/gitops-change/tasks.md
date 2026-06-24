---
schema: gitops
change-type: modificative
blast-radius: medium
slo-impact: <0.01%
change-window: scheduled
author: jane-sre
date: 2024-03-18
---

# GitOps Tasks: Migrate frontend-apps ApplicationSet to cluster generator

**Runbook approved by**: @maria-sre on 2024-03-17
**Change window**: 2024-03-19 Tuesday 14:00-15:00 BRT
**Executor**: @jane-sre
**Backup**: @john-platform

---

## Phase 1: Prerequisites (before change window)

### T1 — Apply cluster labels

- **Owner**: @jane-sre | **ETA**: 15 min | **Deadline**: 2024-03-18 EOD

```bash
kubectl label secret cluster-prod-us-east-1 -n argocd platform/frontend=true
kubectl label secret cluster-prod-eu-west-1 -n argocd platform/frontend=true
kubectl label secret cluster-staging-us-east-1 -n argocd platform/frontend=true
# Verify:
kubectl get secrets -n argocd -l platform/frontend=true | wc -l
# Expected: 4 (3 secrets + header)
```

- [x] Completed 2024-03-18 11:30 BRT

---

### T2 — Prepare and merge PR

- **Owner**: @jane-sre | **ETA**: 20 min | **Deadline**: 2024-03-18 EOD

```bash
git checkout -b feat/frontend-appset-cluster-generator
# edit infrastructure/argocd/appsets/frontend-apps.yaml per design.md
git add infrastructure/argocd/appsets/frontend-apps.yaml
git commit -m "feat(gitops): migrate frontend-apps ApplicationSet to cluster generator"
git push origin feat/frontend-appset-cluster-generator
gh pr create --title "feat(gitops): migrate frontend-apps to cluster generator"
```

**Success criterion**: PR #42 with CI passing and 2 approvals.

- [x] Completed — PR #42 approved by @maria-sre and @john-platform

---

### T3 — Notify stakeholders

- **Owner**: @jane-sre | **ETA**: 5 min | **Deadline**: 2024-03-19 13:00 BRT

```text
#frontend-eng: Platform maintenance tomorrow 14:00-15:00 BRT on ArgoCD frontend-apps.
 No service interruption expected. Questions: @jane-sre

#oncall-sre: Change window scheduled: frontend-apps cluster generator migration.
 Runbook: <link> | PR: #42 | Executor: @jane-sre | Backup: @john-platform
```

- [x] Completed 2024-03-19 13:00 BRT

---

## Phase 2: Change Window — PRE-APPLY

### T4 — Execute PRE-APPLY validations

- **Owner**: @jane-sre | **ETA**: 10 min

- [x] P1 — All ArgoCD pods Running/Ready
- [x] P2 — Labels confirmed on 3 clusters
- [x] P3 — 3 Applications Synced+Healthy before apply
- [x] Proceeding to T5

---

## Phase 3: Change Window — APPLY

### T5 — Merge PR

- **Owner**: @jane-sre | **ETA**: 2 min

```bash
gh pr merge 42 --squash --delete-branch
```

- [x] Completed 14:08 BRT — merge SHA: `a1b2c3d`

---

### T6 — Monitor reconciliation

- **Owner**: @jane-sre (+ @john-platform parallel monitoring)
- **ETA**: 5 min | **Timeout**: 10 min → execute T8 (ROLLBACK)

```bash
watch -n 5 'argocd app list -l app.kubernetes.io/managed-by=frontend-apps'
```

- [x] Completed 14:10 BRT — 3 Applications Synced+Healthy

---

## Phase 4: Change Window — VERIFY

### T7 — Execute VERIFY checks

- [x] V1 — 3 Applications generated ✅
- [x] V2 — All Synced+Healthy ✅
- [x] V3 — Generator confirmed as `clusters` ✅
- [x] Completed 14:13 BRT

---

## Phase 5: Close-out

### T8 — Close change window

```text
#oncall-sre: ✅ Change window completed: frontend-apps migrated to cluster generator.
 3/3 Applications Synced+Healthy. Duration: 13 min. No deviations.
```

**Result**: `success`
**Actual duration**: 13 minutes
**Deviations from runbook**: none
