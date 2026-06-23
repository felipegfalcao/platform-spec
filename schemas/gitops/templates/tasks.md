---
schema: gitops
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# GitOps Tasks: [change title]

<!-- PSPEC:REQUIRED Tasks are executable units derived from the runbook. The runbook must be approved before starting any task. Each task has a single owner, a verifiable command, and a binary success criterion (passed/failed). -->

**Runbook approved by**: `@name` on `YYYY-MM-DD`
**Scheduled change window**: `YYYY-MM-DD HH:MM EST`
**Primary executor**: `@name`
**Backup / pair**: `@name`

---

## Phase 1: Prerequisites (before the change window)

<!-- PSPEC:REQUIRED Prerequisite tasks must be completed BEFORE the change window. -->

### T1 — Configure labels on destination clusters

- **Owner**: @sre-engineer
- **Deadline**: D-1 before the change window
- **Estimate**: 10 minutes
- **Prerequisite for**: T4 (label validation)

```bash
# Apply label to each cluster secret
kubectl label secret cluster-prod-us-east-1 -n argocd platform/frontend=true
kubectl label secret cluster-prod-eu-west-1 -n argocd platform/frontend=true
kubectl label secret cluster-staging-us-east-1 -n argocd platform/frontend=true
```

**Success criterion**: `kubectl get secrets -n argocd -l platform/frontend=true | wc -l` returns `4` (3 secrets + header)

- [ ] Completed
- [ ] Failed — reason: ___

---

### T2 — Prepare and review the PR in the GitOps repository

- **Owner**: @sre-engineer
- **Deadline**: D-1 before the change window
- **Estimate**: 20 minutes

**Steps**:
1. Create branch `feat/frontend-appset-cluster-generator`
2. Edit `infrastructure/argocd/appsets/frontend-apps.yaml` per design.md section 3
3. Verify diff: `git diff HEAD infrastructure/argocd/appsets/frontend-apps.yaml`
4. Open PR with title: `feat(gitops): migrate frontend-apps ApplicationSet to cluster generator`
5. Link PR in impact-analysis as evidence

```bash
git checkout -b feat/frontend-appset-cluster-generator
# edit the file
git add infrastructure/argocd/appsets/frontend-apps.yaml
git commit -m "feat(gitops): migrate frontend-apps ApplicationSet to cluster generator"
git push origin feat/frontend-appset-cluster-generator
gh pr create --title "feat(gitops): migrate frontend-apps ApplicationSet to cluster generator" \
  --body "Platform Spec: $(pwd)/impact-analysis.md"
```

**Success criterion**: PR open with CI passing and at least 1 SRE peer approval.

- [ ] Completed — PR: #___
- [ ] Failed — reason: ___

---

### T3 — Notify stakeholders

- **Owner**: @sre-engineer
- **Deadline**: 1 hour before the change window
- **Estimate**: 5 minutes

```
Message for #frontend-eng:
"[Platform SRE] Planned maintenance tomorrow DD/MM HH:MM-HH:MM EST on ApplicationSet
 frontend-apps. Service will not be interrupted. Questions: @sre-engineer"

Message for #oncall-sre:
"Change window scheduled: frontend-apps ApplicationSet cluster generator migration.
 Runbook: <link> | PR: <link> | Executor: @sre-engineer | Backup: @backup"
```

**Success criterion**: Messages posted and no stakeholder objections.

- [ ] Completed
- [ ] Failed — reason: ___

---

## Phase 2: Change Window — PRE-APPLY

<!-- PSPEC:REQUIRED Execute in exact order. Mark each item before advancing. -->

### T4 — Execute PRE-APPLY validations from the runbook

- **Owner**: @executor
- **Estimate**: 10 minutes
- **Reference**: `runbook.md` section PRE-APPLY

```bash
# P1: ArgoCD health
kubectl get pods -n argocd

# P2: labels on clusters
kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=cluster \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.labels.platform/frontend}{"\n"}{end}'

# P3: current state of Applications
argocd app list -l app.kubernetes.io/managed-by=frontend-apps

# P4: error budget
kubectl get slo frontend-availability -o jsonpath='{.status.errorBudgetRemaining}'
```

**Success criterion**: All P1–P4 validations from the runbook passed without errors.

- [ ] P1 — ArgoCD healthy
- [ ] P2 — Labels confirmed on 3 clusters
- [ ] P3 — 3 Applications in Synced+Healthy before apply
- [ ] P4 — Error budget > 20%
- [ ] Completed
- [ ] STOPPED — reason: ___ (do not advance to T5)

---

## Phase 3: Change Window — APPLY

### T5 — Merge the PR in the GitOps repository

- **Owner**: @executor
- **Estimate**: 2 minutes
- **Prerequisite**: T4 fully completed

```bash
gh pr merge <PR_NUMBER> --squash --delete-branch
```

**Success criterion**: Merge confirmed on GitHub, merge CI passed.

- [ ] Completed — merge SHA: `___`
- [ ] Failed — reason: ___

---

### T6 — Monitor ArgoCD reconciliation

- **Owner**: @executor + @backup (in parallel)
- **Estimate**: 5 minutes
- **Timeout**: If not completed in 10 minutes → execute ROLLBACK (T9)

```bash
# Terminal 1: watch Applications
watch -n 5 'argocd app list -l app.kubernetes.io/managed-by=frontend-apps'

# Terminal 2: controller events
kubectl get events -n argocd --field-selector reason=ReconcileOperation --watch
```

**Success criterion**: 3 Applications listed with STATUS=Synced and HEALTH=Healthy.

- [ ] Completed
- [ ] TIMEOUT — execute T9 (ROLLBACK)

---

## Phase 4: Change Window — VERIFY

### T7 — Execute VERIFY checks from the runbook

- **Owner**: @executor
- **Estimate**: 5 minutes
- **Reference**: `runbook.md` section VERIFY

```bash
# V1: Application count
argocd app list -l app.kubernetes.io/managed-by=frontend-apps --output name | wc -l
# Expected: 3

# V2: status of all Applications
argocd app list -l app.kubernetes.io/managed-by=frontend-apps -o json | \
  jq '[.[] | {name: .metadata.name, sync: .status.sync.status, health: .status.health.status}]'

# V3: pods on each cluster
for ctx in prod-us-east-1 prod-eu-west-1 staging-us-east-1; do
  kubectl --context=$ctx get pods -n frontend -l app=frontend
done

# V5: confirm new generator
kubectl get applicationset frontend-apps -n argocd \
  -o jsonpath='{.spec.generators[0]}' | grep -c clusters
# Expected: 1
```

**Success criterion**: All V1–V5 criteria from the runbook met.

- [ ] V1 — 3 Applications generated
- [ ] V2 — All Synced+Healthy
- [ ] V3 — Pods running on all clusters
- [ ] V4 — No errors in controller log
- [ ] V5 — Generator confirmed as `clusters`
- [ ] Completed
- [ ] FAILED — execute T9 (ROLLBACK)

---

## Phase 5: Post-completion

### T8 — Document outcome and close the change window

- **Owner**: @executor
- **Estimate**: 5 minutes

```
Message for #oncall-sre:
"✅ Change window completed successfully: frontend-apps ApplicationSet migrated to
 cluster generator. 3 Applications in Synced+Healthy across 3 clusters.
 Duration: ___ min. Deviations: [none | describe]"
```

- [ ] Message posted in #oncall-sre
- [ ] Task status updated in this file
- [ ] Outcome recorded in the "result" field below

**Result**: `success | failed-with-rollback`
**Actual duration**: `___ minutes`
**Deviations from runbook**: `none | describe`

---

## Phase 6: Rollback (execute only if needed)

### T9 — Execute ROLLBACK per runbook

- **Owner**: @executor (call @backup if help is needed)
- **Estimate**: 5 minutes
- **Reference**: `runbook.md` section ROLLBACK — follow steps R1–R4 exactly

```bash
# R1: revert the merge commit
git revert <MERGE_COMMIT_SHA> --no-edit
git push origin main
```

**Success criterion**: 3 Applications in Synced+Healthy with `list` generator restored.

- [ ] Rollback completed
- [ ] Stakeholders notified
- [ ] Postmortem opened (required if rollback was needed)
