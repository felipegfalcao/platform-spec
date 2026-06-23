# Context: Rollback Patterns

> Read this file before writing any runbook's ROLLBACK section, and before responding to any incident.

---

## 1. Decision tree: rollback vs. fix forward

```
Problem detected in production
         │
         ▼
Is the cause understood?
├── NO ──────────────────────► ROLLBACK immediately
│                              Understand first, fix after
└── YES
         │
         ▼
Can the fix be applied in < time-to-rollback?
├── YES and fix is low-risk ──► Fix forward
└── NO or fix is risky ───────► ROLLBACK

         After rollback:
         Is rollback complete and service recovered?
         ├── YES ──────────────► Open postmortem, plan proper fix
         └── NO ───────────────► Escalate, consider disaster recovery
```

### When rollback is always correct

- You don't understand what changed
- The blast radius is expanding (more services affected over time)
- Time to diagnose > time to rollback
- On-call is alone without a senior available
- Error budget is nearly exhausted

### When fix forward is acceptable

- The fix is a single-line config change with known impact
- The fix has been tested in staging within the last 24 hours
- You have high confidence in the change (senior SRE pair-reviewing)
- Rolling back would cause equal or more disruption than the current state

---

## 2. ArgoCD / GitOps rollback patterns

### Pattern 1: Git revert (preferred)

The fastest and safest rollback for GitOps changes. Reverts the commit, ArgoCD automatically syncs.

```bash
# Identify the commit that caused the issue
git log --oneline -10
# Example output:
# a1b2c3d feat(gitops): migrate frontend-apps to cluster generator  ← this one
# e4f5g6h chore: update docs

# Revert the specific commit
git revert a1b2c3d --no-edit

# Push to trigger ArgoCD automatic sync
git push origin main

# Monitor sync
watch -n 5 'argocd app list -l app.kubernetes.io/managed-by=frontend-apps'
```

**Expected time**: < 3 minutes from push to ArgoCD sync completion.

### Pattern 2: Hard sync with previous revision (when git revert is slow)

Use when git revert takes too long (PR approval required, branch protection, etc.).

```bash
# Force ArgoCD to sync from a specific git SHA
argocd app sync frontend-prod-us --revision e4f5g6h --force

# For all apps in an ApplicationSet:
for app in $(argocd app list -l app.kubernetes.io/managed-by=frontend-apps -o name); do
  argocd app sync $app --revision e4f5g6h --force
done
```

### Pattern 3: Suspend ApplicationSet (stops generating Applications)

Use when an ApplicationSet is generating bad Applications and you need to stop the damage while diagnosing.

```bash
# Patch the ApplicationSet to pause generation
kubectl patch applicationset frontend-apps -n argocd \
  --type=merge \
  -p '{"spec":{"template":{"metadata":{"annotations":{"argocd.argoproj.io/skip-reconcile":"true"}}}}}'

# After diagnosing, remove the pause:
kubectl patch applicationset frontend-apps -n argocd \
  --type=json \
  -p '[{"op":"remove","path":"/spec/template/metadata/annotations/argocd.argoproj.io~1skip-reconcile"}]'
```

### Pattern 4: Manual sync to previous image (application rollback, not GitOps config)

When the GitOps config is correct but the container image is bad.

```bash
# Force sync with a specific image tag override
argocd app set frontend-prod-us --helm-set image.tag=v1.2.3
argocd app sync frontend-prod-us --force
```

---

## 3. Terraform / IAC rollback patterns

### Pattern 1: Git revert + re-apply (for most IAC changes)

```bash
# Identify the commit
git log --oneline -10

# Revert
git revert <SHA> --no-edit
git push origin main

# Apply the revert (Terraform doesn't auto-apply like ArgoCD)
cd stacks/prod/databases/api-db

# ALWAYS backup state before any rollback
terragrunt state pull > state-backup-$(date +%Y%m%d-%H%M%S).json

# Plan the revert to confirm it does what you expect
terragrunt plan

# Apply
terragrunt apply
```

**Expected time**: 5-30 minutes depending on resource modification time.

### Pattern 2: State manipulation — remove from state without destroying

Use when a resource needs to be removed from Terraform management without deleting it from AWS.

```bash
# Backup first — ALWAYS
terragrunt state pull > state-backup-$(date +%Y%m%d-%H%M%S).json

# List resources in state
terragrunt state list

# Remove specific resource from state (does NOT delete from AWS)
terragrunt state rm 'aws_db_instance.api_db'

# Verify removal
terragrunt state list | grep aws_db_instance
```

**When to use**: Resource was imported into state incorrectly, or you need to move it to a different state file.

### Pattern 3: State manipulation — move resource (rename in state)

```bash
# Backup first
terragrunt state pull > state-backup-$(date +%Y%m%d-%H%M%S).json

# Rename resource in state (useful when refactoring module structure)
terragrunt state mv \
  'module.old_rds.aws_db_instance.this' \
  'module.new_rds.aws_db_instance.this'
```

### Pattern 4: Targeted destroy (selective resource deletion)

Use when a specific resource needs to be recreated. High risk — prefer other options.

```bash
# Backup state
terragrunt state pull > state-backup-$(date +%Y%m%d-%H%M%S).json

# Plan targeted destroy to confirm scope
terragrunt plan -target='aws_db_instance.api_db' -destroy

# Execute targeted destroy (ONLY after reviewing plan)
terragrunt destroy -target='aws_db_instance.api_db' -auto-approve

# Re-apply to recreate
terragrunt apply -target='aws_db_instance.api_db'
```

**Warning**: `-target` can leave state inconsistent. Use with extreme caution and only as a last resort.

---

## 4. Observability rollback patterns

### Pattern 1: Delete alert rule (fastest rollback)

```bash
# Remove the PrometheusRule that is causing alert storm
kubectl delete prometheusrule <rule-name> -n monitoring

# Verify removal
kubectl get prometheusrule <rule-name> -n monitoring
# Expected: "not found"
```

### Pattern 2: Restore previous alert rule version

```bash
# Find previous version in git
git log --oneline alerts/payment-gateway/latency.yaml

# Restore specific version
git checkout <PREVIOUS_SHA> -- alerts/payment-gateway/latency.yaml
kubectl apply -f alerts/payment-gateway/latency.yaml -n monitoring
```

### Pattern 3: Silence an alert during validation (not a rollback, but buys time)

```bash
# Create silence for 1 hour
amtool silence add \
  alertname="PaymentGatewayHighLatency" \
  --comment="Investigating false positive — not a real incident" \
  --duration=1h \
  --alertmanager.url=http://alertmanager.internal

# List active silences
amtool silence query

# Expire silence early if issue resolved
amtool silence expire <SILENCE_ID>
```

---

## 5. Time-to-rollback benchmarks

Use these benchmarks to decide between rollback and fix-forward.

| Change type | Expected rollback time | Notes |
|-------------|----------------------|-------|
| ArgoCD ApplicationSet (git revert) | 2-5 min | ArgoCD auto-syncs after push |
| ArgoCD forced sync to previous SHA | 1-3 min | Bypasses git, faster |
| Terraform in-place modification | 10-30 min | Requires new modification |
| Terraform new resource (additive) | 5-10 min | `terraform destroy -target` |
| RDS instance destroy+recreate | 30-60 min | Avoid at all costs |
| Alert rule removal | < 1 min | `kubectl delete prometheusrule` |
| Alert rule threshold restore | 1-3 min | `kubectl apply` of previous version |

---

## 6. State backup protocol (mandatory before IAC rollback)

```bash
#!/bin/bash
# Run before ANY state manipulation

STACK_PATH=$(pwd)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="state-backup-${TIMESTAMP}.json"

# Pull current state
terragrunt state pull > "$BACKUP_FILE"

# Verify backup is valid JSON
jq . "$BACKUP_FILE" > /dev/null && echo "✅ State backup valid: $BACKUP_FILE" || echo "❌ Backup failed"

# Store backup path for reference
echo "Backup: $(pwd)/$BACKUP_FILE"
```

**Backup retention**: Keep state backups for at least 7 days after a rollback.

---

## 7. Glossary

| Term | Definition |
|------|-----------|
| **Rollback** | Reverting to a previously known good state |
| **Fix forward** | Applying a new change to fix the current bad state, instead of reverting |
| **State manipulation** | Direct modification of the Terraform state file without applying HCL |
| **Targeted destroy** | Destroying a specific resource without affecting the rest of the state |
| **Silence** | A temporary suppression of alerting for specific label matchers in Alertmanager |
| **Suspend ApplicationSet** | Temporarily stopping an ApplicationSet from generating new Applications |
