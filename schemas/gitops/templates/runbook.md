---
schema: gitops
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# GitOps Runbook: [change title]

<!-- PSPEC:REQUIRED This runbook must be written BEFORE execution and reviewed by at least one peer. Commands must be tested in staging before production. Replace all values in <> with real values. -->

**Estimated total duration**: `~30 minutes`
**Rollback window**: `5 minutes`
**On-call required**: `Yes — notify #oncall-sre before starting`

---

## PRE-APPLY

<!-- PSPEC:REQUIRED Execute all validations below before applying any change. Do not proceed if any validation fails. -->

### P1 — Verify ArgoCD health

```bash
# Verify all controllers are healthy
kubectl get pods -n argocd
# Expected: all pods in Running/Ready

# Verify no active sync is in progress on affected Applications
argocd app list -l app.kubernetes.io/managed-by=frontend-apps
# Expected: STATUS=Synced, HEALTH=Healthy for all
```

**STOP if**: Any ArgoCD pod is not Ready, or any Application is in Syncing or Degraded state.

### P2 — Confirm labels on destination clusters

```bash
# List all cluster secrets and their platform/frontend labels
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

**STOP if**: Any cluster appears without the `true` label. Apply the label before proceeding:

```bash
kubectl label secret <cluster-secret-name> -n argocd platform/frontend=true
```

### P3 — Dry-run the ApplicationSet

```bash
# Generate the YAML the ApplicationSet would produce with the new generator
# (requires argocd-cli with --dry-run flag or preview via UI)
argocd appset generate <path-to-new-appset.yaml>
# Verify: number of generated Applications = 3
# Verify: Application names are correct
# Verify: server URLs are correct for each cluster
```

### P4 — Verify existing Applications before the apply

```bash
# Record current state for post-apply comparison
argocd app list -l app.kubernetes.io/managed-by=frontend-apps \
  -o json | jq '[.[] | {name: .metadata.name, status: .status.sync.status, health: .status.health.status}]'
```

**Save this output** — it will be used for post-apply validation.

### P5 — Confirm available error budget

```bash
# Check current SLO status (adapt for your SLO tool)
# Example with Sloth/Pyrra:
kubectl get slo frontend-availability -o jsonpath='{.status.errorBudgetRemaining}'
# Expected: > 20% to proceed without additional approval
```

**STOP if**: Error budget < 10%. Requires SRE Lead approval before proceeding.

---

## APPLY

<!-- PSPEC:REQUIRED Execute the steps below in exact order. Do not skip steps. -->

### A1 — Apply in staging first

```bash
# Confirm the correct branch is checked out
git checkout feat/frontend-appset-cluster-generator
git status  # should show clean working tree

# If staging uses a separate GitOps repo, apply staging first:
# The merge to main triggers automatic sync in staging
# Wait for sync in staging before proceeding to production
```

**If staging and production use the same GitOps repo with targetRevision `main`**, the apply will be simultaneous after the merge. In this case, monitor both in parallel.

### A2 — Merge the PR in the GitOps repository

```bash
# Confirm the PR passed all CI checks
# Merge via GitHub/GitLab UI or:
gh pr merge <PR_NUMBER> --squash --delete-branch
```

### A3 — Monitor ArgoCD reconciliation

```bash
# Monitor ApplicationSet status in real time
watch -n 5 'argocd app list -l app.kubernetes.io/managed-by=frontend-apps'

# In parallel, monitor ApplicationSet events
kubectl get events -n argocd --field-selector reason=ReconcileOperation --watch
```

**Expected reconciliation time**: < 2 minutes after merge.

### A4 — Verify Application generation

```bash
# Confirm the 3 Applications were generated with the correct names
argocd app list -l app.kubernetes.io/managed-by=frontend-apps
# Expected: 3 Applications with status Synced and health Healthy
```

---

## VERIFY

<!-- PSPEC:REQUIRED Objective success criteria. The change is considered successful ONLY when ALL criteria below are met. -->

### V1 — Correct number of Applications

```bash
argocd app list -l app.kubernetes.io/managed-by=frontend-apps --output name | wc -l
```

**Success criterion**: output = `3`

### V2 — All Applications in Synced + Healthy

```bash
argocd app list -l app.kubernetes.io/managed-by=frontend-apps \
  -o json | jq '[.[] | {name: .metadata.name, sync: .status.sync.status, health: .status.health.status}]'
```

**Success criterion**: `sync: "Synced"` and `health: "Healthy"` for ALL Applications.

### V3 — Frontend smoke test on each cluster

```bash
# Verify that frontend pods are Running on each cluster
for ctx in prod-us-east-1 prod-eu-west-1 staging-us-east-1; do
  echo "=== Cluster: $ctx ==="
  kubectl --context=$ctx get pods -n frontend -l app=frontend
done
# Expected: all pods in Running/Ready
```

### V4 — Verify absence of errors in the ArgoCD controller

```bash
kubectl logs -n argocd deployment/argocd-applicationset-controller --tail=50 | grep -i error
# Expected: no error lines related to frontend-apps
```

### V5 — Confirm the ApplicationSet is using the new generator

```bash
kubectl get applicationset frontend-apps -n argocd \
  -o jsonpath='{.spec.generators[0]}'
# Expected: output contains "clusters" and does NOT contain "list"
```

**Maximum time for all criteria**: 10 minutes after A2. If not met within 10 minutes, execute ROLLBACK.

---

## ROLLBACK

<!-- PSPEC:REQUIRED Exact reversal procedure. Must be executable in < 5 minutes. Copy and execute the commands below — do not adapt during an incident. -->

### When to roll back

Execute ROLLBACK immediately if any condition occurs:

- Generated Applications < 3 for more than 2 minutes
- Any Application in `Degraded` or `Unknown` for more than 2 minutes
- Frontend error rate > 1% for 1 consecutive minute
- ApplicationSet controller in error loop (> 5 errors in the log within 1 minute)

### R1 — Revert the commit in the GitOps repository

```bash
# Identify the merge commit
git log --oneline -5

# Revert the merge commit
git revert <MERGE_COMMIT_SHA> --no-edit

# Push to main (triggers automatic ArgoCD reconciliation)
git push origin main
```

**Expected time**: ArgoCD reconciles in < 2 minutes after the push.

### R2 — Force manual sync (if automatic reconciliation does not occur)

```bash
# Force hard refresh of the ApplicationSet
argocd appset delete frontend-apps --yes  # WARNING: also removes Applications
argocd apply -f <path-to-old-appset.yaml>

# OR, if the revert was already committed in git and only a forced sync is needed:
argocd app sync frontend-apps --force
```

**Warning**: Use `argocd appset delete` only if the git revert has already been committed. Never delete without having the previous configuration ready to re-apply.

### R3 — Verify post-rollback state

```bash
# Confirm Applications returned to their original state
argocd app list -l app.kubernetes.io/managed-by=frontend-apps
# Expected: 3 Applications, all Synced + Healthy

# Confirm the generator reverted to list
kubectl get applicationset frontend-apps -n argocd \
  -o jsonpath='{.spec.generators[0]}'
# Expected: output contains "list"
```

### R4 — Communicate the rollback

```bash
# Post in #oncall-sre:
# "⚠️ ROLLBACK executed: frontend-apps ApplicationSet reverted to list generator.
#  Reason: [describe the symptom]. Current state: [Synced/Degraded].
#  Change window closed. Opening postmortem."
```

### R5 — Open a postmortem (if rollback was needed)

If rollback was necessary, the change FAILED. Open an INCIDENT schema with the `postmortem.md` template before attempting the change again.

---

## References

- [context/argocd.md](../../../context/argocd.md) — ArgoCD patterns
- [context/rollback-patterns.md](../../../context/rollback-patterns.md) — rollback decision tree
- [validation/gitops-checklist.md](../../../validation/gitops-checklist.md) — full checklist
