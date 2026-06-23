---
schema: iac
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
destroy-and-recreate: # true | false
state-manipulation: # true | false
affects-other-teams: # true | false
author: # author-name
date: # YYYY-MM-DD
---

# IAC Runbook: [change title]

<!-- PSPEC:REQUIRED Exact commands, tested in staging. Replace all values in <> with real values. This runbook must be executable during an incident at 3am. -->

**Estimated total duration**: `~45 minutes`
**Rollback window**: `20 minutes`
**On-call required**: `Yes — SRE Lead available`

---

## PRE-APPLY

<!-- PSPEC:REQUIRED All validations must pass before any apply. STOP if any one fails. -->

### P1 — Format and validate HCL

```bash
# Check formatting (should produce no diff)
cd infra-repo
terragrunt hclfmt --check --recursive stacks/
# Expected: exit code 0, no files modified

# Validate syntax and configuration
cd stacks/staging/databases/api-db
terragrunt validate
# Expected: "Success! The configuration is valid."
```

**STOP if**: `hclfmt` finds badly formatted files → run `terragrunt hclfmt` to fix and commit before proceeding.

### P2 — Run terraform plan and review output

```bash
cd stacks/staging/databases/api-db

# Generate and save the plan
terragrunt plan -out=tfplan-staging-$(date +%Y%m%d-%H%M%S)

# Verify the plan contains NO destroy or replace
terraform show -json tfplan-staging-* | \
  jq '.resource_changes[] | select(.change.actions | contains(["delete"])) | .address'
# Expected: no output (zero resources being deleted)

# Verify change counts
terraform show tfplan-staging-* | tail -5
# Expected: "Plan: 0 to add, 1 to change, 0 to destroy."
```

**STOP if**: Plan shows `to destroy > 0` or any `-/+`. Review design before proceeding.

### P3 — Security scan with Checkov

```bash
cd stacks/staging/databases/api-db

checkov -d . --compact --quiet \
  --framework terraform \
  --skip-check CKV_AWS_129  # example: skip specific check with documented justification
# Expected: "Passed checks: N, Failed checks: 0, Skipped checks: M"
```

**STOP if**: Checkov reports `Failed checks > 0` for HIGH or CRITICAL severity without a documented suppression justification.

### P4 — Lint with tflint

```bash
cd modules/rds-postgres
tflint --init
tflint
# Expected: zero warnings, zero errors
```

### P5 — Verify state lock

```bash
# Verify the state is not locked
cd stacks/prod/databases/api-db
terragrunt force-unlock --help  # only check syntax, do not execute

# Check DynamoDB lock table
aws dynamodb get-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "bucket-name/stacks/prod/databases/api-db/terraform.tfstate-md5"}}' \
  --region us-east-1
# Expected: empty Item (no active lock)
```

**STOP if**: State is locked. Investigate which process holds the lock before proceeding.

### P6 — Verify error budget

```bash
# Adapt for your SLO tool (Sloth, Pyrra, Nobl9)
kubectl get prometheusrule api-slo-availability -n monitoring \
  -o jsonpath='{.metadata.annotations.platform-spec/error-budget-remaining}'
# Expected: > 20%
```

**STOP if**: Error budget < 10%. Requires SRE Lead approval with a business justification.

---

## APPLY

<!-- PSPEC:REQUIRED Always run staging first. Never apply directly to production. -->

### A1 — Apply in staging

```bash
cd stacks/staging/databases/api-db

# Apply with the tfplan generated in PRE-APPLY (do not generate a new plan now)
terragrunt apply tfplan-staging-*

# Monitor output in real time
# Expected: "Apply complete! Resources: 0 added, 1 changed, 0 destroyed."
```

**Expected apply time in staging**: 2–5 minutes.

### A2 — Wait for RDS modification to complete in staging

```bash
# Monitor modification status
aws rds describe-db-instances \
  --db-instance-identifier api-staging \
  --query 'DBInstances[0].DBInstanceStatus' \
  --region us-east-1

# Monitoring loop (every 30s)
while true; do
  STATUS=$(aws rds describe-db-instances \
    --db-instance-identifier api-staging \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text --region us-east-1)
  echo "$(date): $STATUS"
  [[ "$STATUS" == "available" ]] && break
  sleep 30
done
```

**Expected time**: 5–15 minutes for storage type modification.

### A3 — Validate staging before proceeding to production (see VERIFY below)

**Run VERIFY completely for staging before starting A4.**

### A4 — Plan in production (new plan, do not reuse staging)

```bash
cd stacks/prod/databases/api-db

# Generate new plan for production
terragrunt plan -out=tfplan-prod-$(date +%Y%m%d-%H%M%S)

# Verify again: zero destroy in production too
terraform show -json tfplan-prod-* | \
  jq '.resource_changes[] | select(.change.actions | contains(["delete"])) | .address'
# Expected: no output
```

### A5 — Apply in production

```bash
cd stacks/prod/databases/api-db
terragrunt apply tfplan-prod-*
```

**Notify #oncall-sre before executing this command.**

---

## VERIFY

<!-- PSPEC:REQUIRED Objective criteria. The change is successful only when ALL are met in both environments. -->

### V1 — RDS in `available` state

```bash
for ENV in staging prod; do
  aws rds describe-db-instances \
    --db-instance-identifier api-${ENV} \
    --query 'DBInstances[0].{Status:DBInstanceStatus,StorageType:StorageType,Iops:Iops}' \
    --output table --region us-east-1
done
```

**Success criterion**: `StorageType=gp3`, `Iops=3000` (staging) / `6000` (prod), `Status=available`.

### V2 — API latency at normal levels

```bash
# Query metrics from the last 10 minutes (adapt for your tool)
# Example with awscli CloudWatch:
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ReadLatency \
  --dimensions Name=DBInstanceIdentifier,Value=api-prod \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average \
  --region us-east-1
```

**Success criterion**: `ReadLatency` < 0.002 seconds (2ms), equal to or better than before.

### V3 — Terraform state consistent

```bash
cd stacks/prod/databases/api-db
terragrunt plan
# Expected: "No changes. Your infrastructure matches the configuration."
```

**Success criterion**: Plan shows zero changes after apply.

### V4 — Verify outputs unchanged

```bash
cd stacks/prod/databases/api-db
terragrunt output
# Verify that endpoint, identifier, and port are identical to the previous state
```

---

## ROLLBACK

<!-- PSPEC:REQUIRED IAC rollback is more complex than GitOps. Read each step before executing. -->

### When to roll back

**BEFORE production apply** (A4/A5):
- Apply in staging caused downtime > 2 minutes in staging
- Plan in production shows unexpected destroy

**AFTER production apply**:
- Database status does not return to `available` within 30 minutes
- API latency remains > 3x baseline for 15 minutes
- API error rate > 2% for 5 minutes

### R1 — Rollback modification (revert to gp2)

The in-place modification can be reverted with another modification:

```bash
# Revert HCL to original values
cd infra-repo
git revert HEAD --no-edit  # if the change commit is HEAD
# OR
git checkout <SHA-before-change> -- stacks/prod/databases/api-db/terragrunt.hcl
git checkout <SHA-before-change> -- stacks/staging/databases/api-db/terragrunt.hcl
git checkout <SHA-before-change> -- modules/rds-postgres/variables.tf
git checkout <SHA-before-change> -- modules/rds-postgres/main.tf

git add -A
git commit -m "revert(iac): rollback rds-postgres to gp2 storage type"
git push origin main

# Execute rollback apply (follow the same PRE-APPLY)
cd stacks/prod/databases/api-db
terragrunt plan   # verify plan reverts to gp2
terragrunt apply
```

**Expected rollback time**: 15–25 minutes (new RDS modification).

### R2 — If state became inconsistent

```bash
# Backup state before any manipulation
cd stacks/prod/databases/api-db
terragrunt state pull > state-backup-$(date +%Y%m%d-%H%M%S).json

# Verify what the state says vs what is in AWS
terragrunt plan  # divergences will appear here

# Refresh state to sync with AWS
terragrunt refresh
```

### R3 — Verify post-rollback

```bash
# Confirm the database reverted to gp2
aws rds describe-db-instances \
  --db-instance-identifier api-prod \
  --query 'DBInstances[0].{StorageType:StorageType,Status:DBInstanceStatus}' \
  --output table --region us-east-1
# Expected: StorageType=gp2, Status=available

# Confirm clean plan
cd stacks/prod/databases/api-db
terragrunt plan
# Expected: "No changes."
```

### R4 — Communicate and open postmortem

```
#oncall-sre: "⚠️ IAC ROLLBACK executed: rds-postgres reverted to gp2.
 Reason: [symptom]. Current state: [available/modifying].
 Opening postmortem — do not retry this change without review."
```

---

## References

- [context/terragrunt.md](../../../context/terragrunt.md) — Composite/Component patterns
- [context/rollback-patterns.md](../../../context/rollback-patterns.md) — Terraform rollback decision tree
- [validation/iac-checklist.md](../../../validation/iac-checklist.md) — full checklist
