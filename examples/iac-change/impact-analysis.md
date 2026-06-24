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

# IAC Impact Analysis: Migrate api-db RDS storage from gp2 to gp3

## 1. Change scope

### 1.1 Affected stacks and modules

| Repository path | Module/Resource | Change type |
|----------------|-----------------|-------------|
| `stacks/prod/databases/api-db/terragrunt.hcl` | `modules/rds-postgres` | modificative |
| `stacks/staging/databases/api-db/terragrunt.hcl` | `modules/rds-postgres` | modificative |
| `modules/rds-postgres/variables.tf` | new variables | additive |
| `modules/rds-postgres/main.tf` | resource attributes | modificative |

### 1.2 Affected resources

| Resource address | Type | Action | Destroy+Recreate? |
|-----------------|------|--------|-------------------|
| `aws_db_instance.this` | RDS Instance (prod) | modify | No (in-place) |
| `aws_db_instance.this` | RDS Instance (staging) | modify | No (in-place) |
| `aws_db_instance.replica` | RDS Read Replica (prod) | modify | No (in-place) |

**Total resources**: 3 | **Destroyed**: 0

### 1.3 Affected environments

| Environment | Stack path | Apply order |
|------------|-----------|-------------|
| staging | `stacks/staging/databases/api-db` | First |
| production | `stacks/prod/databases/api-db` | Second (after staging validation) |

## 2. Destroy and recreate

**`destroy-and-recreate: false`**

AWS supports in-place modification of `storage_type` from gp2 to gp3. Confirmed: `storage_type`, `iops`, and `storage_throughput` are **not** ForceNew attributes.

**Stop condition**: If `terraform plan` shows any `-/+` or `destroy`, stop immediately — this analysis is incorrect.

## 3. Downstream dependencies

| Dependent stack | Consumed output | Impact |
|----------------|-----------------|--------|
| `stacks/prod/app/api-backend` | `endpoint`, `port` | None — outputs unchanged |
| `stacks/prod/monitoring/rds-alerts` | `identifier` | None — identifier unchanged |

No downstream stacks need to be re-applied.

## 4. Blast radius

**Classified as**: `medium`

**Failure scenario: I/O degradation during modification window**

- Symptom: RDS in `modifying` state, queries see increased latency
- Duration: 5–15 minutes (AWS modification time)
- Affected services: api-backend (writes), data-pipeline (reads)
- Recovery: Wait for modification to complete — cannot be aborted mid-flight

**Why not `high`?** No destroy+recreate. Instance stays available during modification with degraded I/O. Rollback is a second modification back to gp2 (10–20 additional minutes).

## 5. SLO impact

**Classified as**: `0.01-0.1%`

| SLO | Target | Monthly budget | Change impact |
|-----|--------|----------------|---------------|
| API Availability | 99.9% | 43.8 min | ~10 min (I/O degradation window) |

**Calculation**: 10 min / 43.8 min = 22.8% of monthly budget.
**Action required**: SRE Lead budget approval — consumed > 20% in single change.

**Approved by**: @maria-sre on 2024-03-19. Justification: performance degradation already active (ongoing SLO impact from slow queries).

## 6. Change window

**Type**: `required`

**Window**: Sunday 2024-03-24 02:00–04:00 BRT
**Duration**: 45 minutes (staging: 15 min + prod: 30 min)
**SRE Lead on-call**: @maria-sre (available)

## 7. Rollback triggers

**STOP before prod apply if**:

- Staging apply caused downtime > 2 minutes
- `terraform plan` on prod shows any `-/+` for RDS instance

**ROLLBACK post-apply if**:

- API p99 remains > 500ms for 10 consecutive minutes
- API error rate > 2% for 2 consecutive minutes
