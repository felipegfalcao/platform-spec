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

# IAC Tasks: [change title]

<!-- PSPEC:REQUIRED Runbook approved before starting. Staging always before production. -->

**Runbook approved by**: `@name` on `YYYY-MM-DD`
**Scheduled change window**: `YYYY-MM-DD HH:MM EST`
**Executor**: `@name`
**Backup**: `@name`
**On-call SRE Lead**: `@name`

---

## Phase 1: Development and validation (before the change window)

### T1 — Implement HCL changes

- **Owner**: @dev
- **Estimate**: 30 minutes
- **Environment**: local / dev branch

```bash
git checkout -b feat/rds-gp3-migration
# Edit modules/rds-postgres/variables.tf — add 3 new variables
# Edit modules/rds-postgres/main.tf — use new variables in the resource
# Edit stacks/prod/databases/api-db/terragrunt.hcl — new inputs
# Edit stacks/staging/databases/api-db/terragrunt.hcl — new inputs
```

**Success criterion**: `terragrunt validate` passes on both stacks.

- [ ] Completed
- [ ] Failed — reason: ___

---

### T2 — Run quality validations

- **Owner**: @dev
- **Estimate**: 15 minutes

```bash
# Formatting
terragrunt hclfmt --check --recursive stacks/
# Lint
cd modules/rds-postgres && tflint
# Security
cd stacks/staging/databases/api-db && checkov -d . --compact --quiet
```

**Success criterion**: hclfmt no diff, tflint zero warnings, checkov zero failed HIGH/CRITICAL.

- [ ] hclfmt clean
- [ ] tflint clean
- [ ] checkov clean
- [ ] Completed

---

### T3 — Generate and review terraform plan in staging

- **Owner**: @dev + review by @peer
- **Estimate**: 20 minutes

```bash
cd stacks/staging/databases/api-db
terragrunt plan -out=tfplan-staging
terraform show tfplan-staging
```

**Success criterion**: Plan shows `1 changed, 0 destroyed`. Zero resources with `-/+`.

- [ ] Plan generated and saved
- [ ] Zero destroy in plan
- [ ] Plan reviewed and approved by @peer
- [ ] Completed

---

### T4 — Open and approve PR

- **Owner**: @dev
- **Deadline**: D-1

```bash
git add -A
git commit -m "feat(iac): migrate rds-postgres to gp3 storage type"
git push origin feat/rds-gp3-migration
gh pr create --title "feat(iac): migrate rds-postgres to gp3 storage type"
```

**Success criterion**: PR with 2 approvals, CI passing (including `checkov` and `tflint`).

- [ ] PR opened — number: #___
- [ ] 2 approvals received
- [ ] CI passing
- [ ] Completed

---

## Phase 2: Change Window — Staging

### T5 — Execute PRE-APPLY in staging

- **Owner**: @executor
- **Estimate**: 10 minutes
- **Reference**: runbook.md section PRE-APPLY (P1 to P6)

- [ ] P1 — hclfmt and validate OK
- [ ] P2 — zero-destroy plan confirmed
- [ ] P3 — checkov clean
- [ ] P4 — tflint clean
- [ ] P5 — state not locked
- [ ] P6 — error budget > 20%
- [ ] Completed — proceed to T6
- [ ] STOPPED at P___ — reason: ___ (do not advance)

---

### T6 — Apply in staging

- **Owner**: @executor
- **Estimate**: 15 minutes (including wait for modification)

```bash
cd stacks/staging/databases/api-db
terragrunt apply tfplan-staging
```

Wait for `available` status:
```bash
aws rds wait db-instance-available --db-instance-identifier api-staging --region us-east-1
```

- [ ] Apply completed without errors
- [ ] RDS in `available` status
- [ ] Completed

---

### T7 — Verify staging (VERIFY)

- **Owner**: @executor
- **Reference**: runbook.md section VERIFY (V1 to V4)

- [ ] V1 — StorageType=gp3, Iops=3000, Status=available
- [ ] V2 — Latency at normal levels (or better)
- [ ] V3 — Post-apply plan shows zero changes
- [ ] V4 — Outputs unchanged
- [ ] Completed — proceed to Phase 3
- [ ] FAILED — execute T10 (ROLLBACK STAGING)

---

## Phase 3: Change Window — Production

### T8 — Generate production plan and notify

- **Owner**: @executor
- **Estimate**: 5 minutes

```bash
cd stacks/prod/databases/api-db
terragrunt plan -out=tfplan-prod
terraform show tfplan-prod | tail -10
# Verify: "0 to destroy"
```

Notify before apply:
```
#oncall-sre: "Starting IAC prod apply — rds-postgres gp3 migration. Runbook: <link>"
```

- [ ] Production plan generated with zero destroy
- [ ] Stakeholders notified
- [ ] Completed

---

### T9 — Apply in production

- **Owner**: @executor (with @backup monitoring)
- **Estimate**: 20 minutes

```bash
cd stacks/prod/databases/api-db
terragrunt apply tfplan-prod
aws rds wait db-instance-available --db-instance-identifier api-prod --region us-east-1
```

Monitor in parallel:
```bash
# Terminal 2: CloudWatch RDS
watch -n 30 'aws rds describe-db-instances \
  --db-instance-identifier api-prod \
  --query "DBInstances[0].DBInstanceStatus" --output text --region us-east-1'

# Terminal 3: API error rate (adapt for your observability tool)
watch -n 10 'kubectl top pods -n api --sort-by cpu'
```

- [ ] Apply completed without errors
- [ ] RDS in `available` status
- [ ] No error spike in the API during modification
- [ ] Completed

---

### T9b — VERIFY in production

- **Owner**: @executor
- **Reference**: runbook.md section VERIFY

- [ ] V1 — StorageType=gp3, Iops=6000, Status=available
- [ ] V2 — API latency normal or improved
- [ ] V3 — Post-apply plan shows zero changes
- [ ] V4 — Outputs unchanged
- [ ] Completed — close change window
- [ ] FAILED — execute T10 (ROLLBACK PROD)

---

## Phase 4: Post-completion

### T9c — Close the change window

```
#oncall-sre: "✅ Change window completed: rds-postgres migrated to gp3 in staging and production.
 Duration: ___ min. StorageType=gp3, Iops=6000 confirmed.
 Deviations: [none | describe]"
```

**Result**: `success | failed-with-rollback`
**Actual duration**: `___ minutes`
**Deviations**: `none | describe`

---

## Phase 5: Rollback (only if needed)

### T10 — Execute ROLLBACK

- **Reference**: runbook.md section ROLLBACK

```bash
git revert HEAD --no-edit
git push origin main
# Wait for CI and apply manually if needed
```

- [ ] Rollback staging (if needed)
- [ ] Rollback production (if needed)
- [ ] RDS reverted to gp2 in `available` status
- [ ] Post-rollback plan shows zero changes
- [ ] Stakeholders notified
- [ ] Postmortem opened
