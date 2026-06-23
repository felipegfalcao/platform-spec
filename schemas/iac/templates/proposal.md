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

# IAC Proposal: [change title]

<!-- PSPEC:REQUIRED Replace the title with a precise description. Example: "Migrate RDS PostgreSQL from gp2 to gp3 storage type in production" -->

## Problem

<!-- PSPEC:REQUIRED Describe the current infrastructure problem. Include: module/resource with the issue, incorrect behavior or limitation, operational impact. -->

**Example**: The `rds-postgres` module in `stacks/prod/databases/api-db/terragrunt.hcl` uses `gp2` storage type with 100 GB. The database is consistently hitting 3000 IOPS (the gp2 limit for 100 GB), causing performance degradation on listing queries. Current cost: $0.115/GB-month. Equivalent gp3 cost: $0.08/GB-month with configurable IOPS.

## Motivation

<!-- PSPEC:REQUIRED Explain the current impact and urgency. Include observable data. -->

**Example**: p99 of queries on the `/api/v2/products` endpoint rose from 120ms to 850ms over the last 7 days (dashboard: [link]). The product team reported 18% checkout abandonment. Monthly gp2 cost: $138/month vs equivalent gp3: $95/month (saving $43/month + performance improvement).

## Proposed solution

<!-- PSPEC:REQUIRED Describe the infrastructure change at the design level — what will be changed, not exactly how. -->

**Example**: Modify the `rds-postgres` module to use `storage_type = "gp3"` with `iops = 6000` and `storage_throughput = 250` MiB/s. The gp2 to gp3 change is supported by AWS as an in-place modification and does NOT require destroy+recreate in most cases — verify via `terraform plan` before applying.

## Impact on other teams

<!-- PSPEC:REQUIRED If affects-other-teams: true, list the affected teams and how they will be informed. -->

| Team | Consumed resource | Expected impact | Communication |
|------|------------------|-----------------|---------------|
| Product team | `api-db` database | Performance improvement, no downtime | Slack #product-eng |
| Data team | `api-db` read replica | Same — read replica follows modification | Slack #data-eng |

## Alternatives considered

<!-- PSPEC:OPTIONAL -->

| Alternative | Reason discarded |
|-------------|-----------------|
| Increase IOPS on gp2 (provisioned) | Higher cost than gp3: $0.20/IOPS vs gp3 baseline |
| Optimize queries (no infra change) | Already investigated — bottleneck is I/O, not query plan |
| Migrate to Aurora Serverless | High risk, engine change, out of scope this quarter |

## Expected impact

<!-- PSPEC:REQUIRED -->

- p99 of queries back to < 150ms (historical baseline)
- Available IOPS: 6000 vs current 3000
- Cost reduction of $43/month
- Zero downtime (AWS supports in-place storage type modification)

## Required approvals

| Role | Name | Status |
|------|------|--------|
| SRE Lead | | Pending |
| Eng Manager (cost) | | Pending |

## Dependencies

<!-- PSPEC:OPTIONAL -->

- [ ] RDS maintenance window: IOPS modifications can cause up to 10 min of degradation
- [ ] Read replica: verify whether `apply_immediately = true` is safe or should wait for maintenance window

## Related links

- Performance dashboard:
- Product ticket:
- AWS gp2→gp3 documentation:
