---
schema: iac
change-type: modificative
blast-radius: medium
slo-impact: 0.01-0.1%
change-window: required
destroy-and-recreate: false
state-manipulation: false
affects-other-teams: true
author: bob-sre
date: 2024-03-20
---

# IAC Runbook: Migrate api-db RDS storage from gp2 to gp3

**Estimated duration**: ~45 minutes | **Rollback window**: 20 minutes
**On-call**: SRE Lead @maria-sre available during entire window

---

## PRE-APPLY

### P1 — Format, validate, quality checks

```bash
cd infra-repo
terragrunt hclfmt --check --recursive stacks/
# Expected: exit 0, no diff

cd stacks/staging/databases/api-db && terragrunt validate
# Expected: "Success! The configuration is valid."

checkov -d . --compact --quiet --framework terraform
# Expected: 0 Failed checks (HIGH/CRITICAL)

cd modules/rds-postgres && tflint
# Expected: 0 errors, 0 warnings
```

### P2 — Generate and review staging plan

```bash
cd stacks/staging/databases/api-db
terragrunt plan -out=tfplan-staging-20240324-0200

terraform show -json tfplan-staging-20240324-0200 | \
  jq '.resource_changes[] | select(.change.actions | contains(["delete"])) | .address'
# Expected: no output (zero destroys)

terraform show tfplan-staging-20240324-0200 | tail -5
# Expected: "Plan: 0 to add, 1 to change, 0 to destroy."
```

**STOP if**: Plan shows any `-/+` or `to destroy > 0`.

### P3 — Verify state lock and error budget

```bash
aws dynamodb get-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "acme-tfstate/stacks/staging/databases/api-db/terraform.tfstate-md5"}}' \
  --region us-east-1
# Expected: empty Item (no active lock)
```

---

## APPLY — Staging

### A1 — Backup state and apply

```bash
cd stacks/staging/databases/api-db
terragrunt state pull > state-backup-staging-$(date +%Y%m%d-%H%M%S).json

terragrunt apply tfplan-staging-20240324-0200
# Expected: "Apply complete! Resources: 0 added, 1 changed, 0 destroyed."
```

### A2 — Wait for RDS modification

```bash
aws rds wait db-instance-available \
  --db-instance-identifier api-staging \
  --region us-east-1
# This command blocks until status = available (up to 30 min)
```

### A3 — Verify staging (all criteria must pass before proceeding to prod)

```bash
aws rds describe-db-instances \
  --db-instance-identifier api-staging \
  --query 'DBInstances[0].{Status:DBInstanceStatus,StorageType:StorageType,Iops:Iops}' \
  --output table --region us-east-1
# Expected: StorageType=gp3, Iops=3000, Status=available

cd stacks/staging/databases/api-db && terragrunt plan
# Expected: "No changes. Your infrastructure matches the configuration."
```

---

## APPLY — Production

### A4 — Generate fresh prod plan

```bash
cd stacks/prod/databases/api-db
terragrunt state pull > state-backup-prod-$(date +%Y%m%d-%H%M%S).json
terragrunt plan -out=tfplan-prod-20240324-0230

terraform show -json tfplan-prod-20240324-0230 | \
  jq '.resource_changes[] | select(.change.actions | contains(["delete"])) | .address'
# Expected: no output
```

Notify `#oncall-sre`: "Starting prod apply — RDS gp3 migration."

### A5 — Apply prod

```bash
terragrunt apply tfplan-prod-20240324-0230
aws rds wait db-instance-available --db-instance-identifier api-prod --region us-east-1
```

---

## VERIFY

```bash
# Prod RDS status
aws rds describe-db-instances \
  --db-instance-identifier api-prod \
  --query 'DBInstances[0].{Status:DBInstanceStatus,StorageType:StorageType,Iops:Iops}' \
  --output table --region us-east-1
# Expected: StorageType=gp3, Iops=6000, Status=available

# Plan clean
cd stacks/prod/databases/api-db && terragrunt plan
# Expected: "No changes."

# API latency (check dashboard)
# Expected: p99 back to < 200ms within 10 min of modification completing
```

---

## ROLLBACK

### When to rollback

- Staging caused > 2 minutes of downtime → STOP before prod
- Prod modification stuck for > 30 minutes → Page AWS support
- API p99 > 500ms for 10 minutes after modification completed → rollback to gp2

### R1 — Rollback to gp2

```bash
cd infra-repo
git revert HEAD --no-edit
git push origin main

cd stacks/prod/databases/api-db
terragrunt plan  # verify reverts to gp2
terragrunt apply
aws rds wait db-instance-available --db-instance-identifier api-prod --region us-east-1
```

### R2 — Verify rollback

```bash
aws rds describe-db-instances \
  --db-instance-identifier api-prod \
  --query 'DBInstances[0].{StorageType:StorageType,Status:DBInstanceStatus}' \
  --output table --region us-east-1
# Expected: StorageType=gp2, Status=available
```
