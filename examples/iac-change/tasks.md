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

# IAC Tasks: Migrate api-db RDS storage from gp2 to gp3

**Runbook approved by**: @maria-sre on 2024-03-21
**Change window**: 2024-03-24 Sunday 02:00–04:00 BRT
**Executor**: @bob-sre | **Backup**: @jane-sre | **SRE Lead on-call**: @maria-sre

---

## Phase 1: Development (before change window)

### T1 — Implement HCL changes

- **Owner**: @bob-sre | **ETA**: 45 min | **Deadline**: 2024-03-22 EOD

```bash
git checkout -b feat/rds-gp3-migration
# Edit modules/rds-postgres/variables.tf — add 3 variables
# Edit modules/rds-postgres/main.tf — use new variables
# Edit stacks/prod/databases/api-db/terragrunt.hcl — add gp3 inputs
# Edit stacks/staging/databases/api-db/terragrunt.hcl — add gp3 inputs
cd stacks/staging/databases/api-db && terragrunt validate
```

- [x] Completed 2024-03-22 14:30 BRT

---

### T2 — Quality checks and plan review

- **Owner**: @bob-sre | **ETA**: 20 min

```bash
terragrunt hclfmt --check --recursive stacks/
cd modules/rds-postgres && tflint
cd stacks/staging/databases/api-db && checkov -d . --compact --quiet
cd stacks/staging/databases/api-db && terragrunt plan
```

- [x] hclfmt clean
- [x] tflint clean
- [x] checkov clean
- [x] Plan: 0 add, 1 change, 0 destroy ✅
- [x] Completed

---

### T3 — Open and merge PR

- **Owner**: @bob-sre | **Deadline**: 2024-03-23 EOD

```bash
git commit -m "feat(iac): migrate rds-postgres to gp3 storage type"
git push origin feat/rds-gp3-migration
gh pr create --title "feat(iac): migrate api-db RDS from gp2 to gp3"
```

- [x] PR #89 merged — 2 approvals (@maria-sre, @jane-sre), CI passing

---

## Phase 2: Change Window — Staging

### T4 — PRE-APPLY validations in staging

- **Owner**: @bob-sre | **ETA**: 10 min

- [x] P1 — hclfmt, validate, checkov, tflint all clean
- [x] P2 — Plan confirms 0 destroy, 1 change
- [x] P3 — State lock free
- [x] Proceeding to T5

---

### T5 — Apply in staging

- **Owner**: @bob-sre | **ETA**: 20 min

```bash
cd stacks/staging/databases/api-db
terragrunt state pull > state-backup-staging-20240324-020000.json
terragrunt apply tfplan-staging-20240324-0200
aws rds wait db-instance-available --db-instance-identifier api-staging --region us-east-1
```

- [x] Apply complete: 0 added, 1 changed, 0 destroyed
- [x] RDS status: available (StorageType=gp3, Iops=3000) ✅
- [x] Plan post-apply: No changes ✅
- [x] Proceeding to prod

---

## Phase 3: Change Window — Production

### T6 — Generate prod plan and notify

- **Owner**: @bob-sre | **ETA**: 5 min

```bash
cd stacks/prod/databases/api-db
terragrunt state pull > state-backup-prod-20240324-023000.json
terragrunt plan -out=tfplan-prod-20240324-0230
terraform show tfplan-prod-20240324-0230 | tail -3
# Confirmed: 0 to add, 1 to change, 0 to destroy
```

Notified `#oncall-sre` 02:31 BRT: "Starting prod apply."

- [x] Completed

---

### T7 — Apply in production

- **Owner**: @bob-sre (+ @maria-sre monitoring) | **ETA**: 25 min

```bash
cd stacks/prod/databases/api-db
terragrunt apply tfplan-prod-20240324-0230
aws rds wait db-instance-available --db-instance-identifier api-prod --region us-east-1
```

- [x] Apply complete: 0 added, 1 changed, 0 destroyed
- [x] RDS status: available (StorageType=gp3, Iops=6000) ✅
- [x] API p99 latency: 145ms (was 850ms) ✅
- [x] Plan post-apply: No changes ✅

---

## Phase 4: Close-out

```text
#oncall-sre: ✅ Change window completed: api-db migrated to gp3 in staging and prod.
 StorageType=gp3, Iops=6000 confirmed. API p99: 145ms (was 850ms).
 Duration: 47 min. Cost savings: $86/month. No deviations from runbook.
```

**Result**: `success`
**Actual duration**: 47 minutes
**Deviations**: none
