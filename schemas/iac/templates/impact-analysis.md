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

# IAC Impact Analysis: [change title]

<!-- PSPEC:REQUIRED Fill with real data. Run terraform plan before completing sections 3 and 4. -->

## 1. Change scope

### 1.1 Affected stacks and modules

<!-- PSPEC:REQUIRED List exact paths in the repository. -->

| Repository path | Module/Resource | Change type |
|----------------|-----------------|-------------|
| `stacks/prod/databases/api-db/terragrunt.hcl` | `modules/rds-postgres` | modificative |
| `stacks/staging/databases/api-db/terragrunt.hcl` | `modules/rds-postgres` | modificative |

### 1.2 Affected resources

<!-- PSPEC:REQUIRED List each Terraform resource that will be created, modified, or destroyed. Use the resource address from the terraform state. -->

| Resource Address | Type | Action | Destroy+Recreate? |
|-----------------|------|--------|--------------------|
| `aws_db_instance.api_db` | AWS RDS Instance | modify | No (in-place) |
| `aws_db_instance.api_db_replica` | AWS RDS Read Replica | modify | No (in-place) |

**Total resources affected**: 2
**Resources destroyed and recreated**: 0

### 1.3 Affected environments

| Environment | Stack | Execute first? |
|-------------|-------|---------------|
| staging | `stacks/staging/databases/api-db` | Yes |
| production | `stacks/prod/databases/api-db` | Second (after staging validation) |

## 2. Destroy and recreate

<!-- PSPEC:REQUIRED This section is critical. A mistake here can cause data loss. -->

**`destroy-and-recreate: false`**

**Justification**: AWS supports in-place modification of `storage_type` from gp2 to gp3 without replacing the resource. Confirm via `terraform plan` — if the plan shows `-/+` (replace), this analysis is incorrect and the change requires revision.

**If the plan shows replace**: Stop immediately and update this impact-analysis with `destroy-and-recreate: true` and a mandatory data backup section.

### 2.1 Known ForceNew attributes of the resource

The following `aws_db_instance` attributes cause destroy+recreate if modified:
- `engine` (e.g., from postgres to mysql)
- `engine_version` (major version bump)
- `identifier` (database name)
- `db_name` (database name)

**Attributes we ARE modifying**: `storage_type`, `iops`, `storage_throughput` — none of them are ForceNew.

## 3. Downstream dependencies

<!-- PSPEC:REQUIRED Map who depends on the resources being modified — other Terraform modules, ApplicationSets, services. -->

### 3.1 Terraform dependencies

| Dependent stack | Dependency type | Consumed output |
|-----------------|----------------|-----------------|
| `stacks/prod/app/api-backend` | `dependency.db.outputs.endpoint` | connection string |
| `stacks/prod/monitoring/rds-alerts` | `dependency.db.outputs.identifier` | resource name for alerts |

**Impact on dependencies**: Modifications to `storage_type` and `iops` do NOT change outputs (`endpoint`, `identifier`, `port`). Downstream dependencies are not affected.

### 3.2 Application dependencies

| Service | How it consumes | Expected impact |
|---------|----------------|-----------------|
| api-backend (EKS) | Connection string via Secret | None — endpoint does not change |
| data-pipeline | Read replica endpoint | None — endpoint does not change |

## 4. State change

<!-- PSPEC:REQUIRED If state-manipulation: true, document each required state operation. -->

**`state-manipulation: false`**

No state manipulation required. The change is applied via a normal terraform apply.

**If it were needed** (example for documentation):
```bash
# Never run without a state backup first
terraform state pull > state-backup-$(date +%Y%m%d-%H%M%S).json

# Example of mv (rename resource in state)
terraform state mv 'aws_db_instance.old_name' 'aws_db_instance.new_name'

# Example of rm (remove from state without destroying)
terraform state rm 'aws_db_instance.orphaned'
```

## 5. Blast radius

<!-- PSPEC:REQUIRED -->

**Blast radius classified as**: `medium`

### 5.1 Failure scenario: modification causes I/O unavailability

**Symptom**: RDS in `modifying` state, queries fail with connection timeout.
**Estimated duration**: 5–15 minutes (AWS performance during modification).
**Affected services**: api-backend (degraded writes), data-pipeline (degraded reads).
**Detection**: CloudWatch RDS `DatabaseConnections` + SLO alert.
**Recovery**: Wait for the modification to complete (there is no rollback of an in-progress in-place modification).

### 5.2 Failure scenario: terraform plan shows unexpected replace

**Symptom**: `terraform plan` output contains `-/+` for the RDS instance.
**Immediate action**: STOP the apply. Do not execute a plan with replace.
**Recovery**: Review HCL, identify the incorrect ForceNew attribute, update the design.

### 5.3 Why not `high`?

The modification is in-place, without destroy+recreate. The greatest risk is temporary I/O degradation during the AWS modification window (5–15 min), not a total outage. The database continues accepting connections during modification.

## 6. SLO impact

<!-- PSPEC:REQUIRED -->

**SLO impact classified as**: `0.01-0.1%`

| SLO | Target | Monthly error budget | Impact of this change |
|-----|--------|---------------------|-----------------------|
| API Availability | 99.9% | 43.8 min | ~10 min (worst case modification) |
| API Latency p99 | 200ms | N/A | Temporarily worse during modification |

**Calculation**: 10 min of degradation / 43.8 min of total budget = 22.8% of monthly budget.
**Note**: Running during low-traffic hours reduces the real SLO impact.

**Requires budget approval?** Yes — impact > 0.1% requires SRE Lead confirmation.

## 7. Change window

**Change window**: `required`

**Justification**: Medium blast radius + SLO impact > 0.1% requires a formal change window.

**Recommended window**: Sunday 2am–4am EST (traffic ~15% of peak)
**Estimated duration**: 45 minutes total (staging: 15 min + production: 30 min)
**On-call notified**: Yes — SRE Lead must be available

## 8. Rollback trigger

<!-- PSPEC:REQUIRED -->

Execute IMMEDIATE STOP (before production apply) if:
- Apply in staging caused downtime > 2 minutes in staging
- `terraform plan` in production shows `-/+` for the RDS instance
- CloudWatch `CPUUtilization` > 90% before the apply (database already degraded)

Execute ROLLBACK post-apply if:
- API p99 latency remains above 500ms for more than 10 minutes
- API error rate exceeds 2% for 2 consecutive minutes

**Rollback procedure**: see `runbook.md` section ROLLBACK.
**Note**: Rollback of an RDS in-place modification = a new modification back to gp2 (may take an additional 10–20 min).
