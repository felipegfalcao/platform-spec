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

# IAC Proposal: Migrate api-db RDS storage from gp2 to gp3

## Problem

The `rds-postgres` module in `stacks/prod/databases/api-db` uses `storage_type = "gp2"` with 100 GB. The instance is consistently hitting 3,000 IOPS (the gp2 maximum for 100 GB), causing query latency degradation on the `/api/v2/products` endpoint.

## Motivation

The `/api/v2/products` p99 latency rose from 120ms to 850ms over the last 7 days (dashboard: grafana/d/api-perf). Product team reports 18% cart abandonment increase. Current gp2 cost: $138/month vs gp3 equivalent: $95/month.

## Proposed solution

Change the `rds-postgres` module to support `storage_type`, `iops`, and `storage_throughput` as input variables. Configure `stacks/prod/databases/api-db` with `gp3`, `6000` IOPS, and `250 MiB/s` throughput. AWS supports in-place modification from gp2 to gp3 — no destroy+recreate required.

## Teams affected

| Team | Resource | Expected impact | Communication |
|------|----------|-----------------|---------------|
| Product | api-db | Performance improvement, no downtime | `#product-eng` |
| Data | Read replica | Same improvement | `#data-eng` |

## Alternatives considered

| Alternative | Reason discarded |
|-------------|-----------------|
| gp2 with provisioned IOPS | Higher cost: $0.20/IOPS vs gp3 baseline |
| Query optimization only | Investigated — bottleneck is I/O, not query plan |

## Expected outcome

- p99 latency back to < 150ms
- IOPS: 6,000 vs 3,000 (2× improvement)
- Cost reduction: $86/month across prod instances
- Zero downtime (in-place modification)

## Required approvals

| Role | Name | Status |
|------|------|--------|
| SRE Lead | @maria-sre | ✅ Approved 2024-03-19 |
| Eng Manager | @david-em | ✅ Approved 2024-03-19 (cost approval) |
