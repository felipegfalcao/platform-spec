---
schema: gitops
change-type: modificative
blast-radius: medium
slo-impact: <0.01%
change-window: scheduled
author: jane-sre
date: 2024-03-18
---

# GitOps Runbook: Migrate frontend-apps ApplicationSet to cluster generator

**Estimated total duration**: ~30 minutes
**Rollback window**: 5 minutes
**On-call required**: Yes — notify `#oncall-sre` before starting

---

## PRE-APPLY

### P1 — Verify ArgoCD health

```bash
kubectl get pods -n argocd
# Expected: all pods Running/Ready

argocd app list -l app.kubernetes.io/managed-by=frontend-apps
# Expected: 3 Applications, STATUS=Synced, HEALTH=Healthy
```

**STOP if**: Any ArgoCD pod is not Ready, or any Application is Syncing/Degraded.

### P2 — Confirm cluster labels

```bash
kubectl get secrets -n argocd \
  -l argocd.argoproj.io/secret-type=cluster \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.labels.platform/frontend}{"\n"}{end}'
```

**Expected output**:

```text
cluster-prod-us-east-1      true
cluster-prod-eu-west-1      true
cluster-staging-us-east-1   true
```

**STOP if**: Any cluster missing the `true` label. Apply the label first:

```bash
kubectl label secret <cluster-secret-name> -n argocd platform/frontend=true
```

### P3 — Record pre-apply state

```bash
argocd app list -l app.kubernetes.io/managed-by=frontend-apps \
  -o json | jq '[.[] | {name: .metadata.name, status: .status.sync.status}]'
# Save this output for comparison
```

---

## APPLY

### A1 — Merge PR into GitOps repository

```bash
gh pr merge 42 --squash --delete-branch
```

### A2 — Monitor ArgoCD reconciliation

```bash
watch -n 5 'argocd app list -l app.kubernetes.io/managed-by=frontend-apps'
```

Expected time for reconciliation: < 2 minutes after merge.

---

## VERIFY

### V1 — Application count correct

```bash
argocd app list -l app.kubernetes.io/managed-by=frontend-apps --output name | wc -l
```

**Success criterion**: output = `3`

### V2 — All Applications Synced + Healthy

```bash
argocd app list -l app.kubernetes.io/managed-by=frontend-apps \
  -o json | jq '[.[] | {name: .metadata.name, sync: .status.sync.status, health: .status.health.status}]'
```

**Success criterion**: `sync: "Synced"` and `health: "Healthy"` for all 3 Applications.

### V3 — Generator confirmed as cluster type

```bash
kubectl get applicationset frontend-apps -n argocd \
  -o jsonpath='{.spec.generators[0]}' | grep -c clusters
```

**Success criterion**: output = `1`

**Maximum time to meet all criteria**: 10 minutes after merge. If not met, execute ROLLBACK.

---

## ROLLBACK

### When to rollback

- Generated Applications < 3 for more than 2 minutes
- Any Application enters `Degraded` or `Unknown` state
- Frontend error rate > 1% for 1 consecutive minute

### R1 — Revert merge commit

```bash
git log --oneline -3
git revert <MERGE_COMMIT_SHA> --no-edit
git push origin main
```

ArgoCD auto-syncs within 2 minutes of push.

### R2 — Verify rollback

```bash
argocd app list -l app.kubernetes.io/managed-by=frontend-apps
# Expected: 3 Applications, Synced + Healthy

kubectl get applicationset frontend-apps -n argocd \
  -o jsonpath='{.spec.generators[0]}' | grep -c list
# Expected: 1 (generator is back to list)
```

### R3 — Communicate

Post in `#oncall-sre`:

```text
⚠️ ROLLBACK executed: frontend-apps ApplicationSet reverted to list generator.
Reason: [describe symptom]. Current state: [Synced/Degraded].
Change window closed. Opening postmortem.
```
