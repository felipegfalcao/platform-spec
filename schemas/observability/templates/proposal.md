---
schema: observability
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# Observability Proposal: [change title]

<!-- PSPEC:REQUIRED -->

## Observability problem

<!-- PSPEC:REQUIRED Describe the concrete gap or problem. Be specific: which service lacks coverage, which alert is generating false positives, which dashboard is outdated. -->

**Example**: The `payment-gateway` service has no latency alert for successful requests. We currently have an error rate alert, but a performance degradation (slow requests that do not fail) does not trigger any pager. Incident INC-2024-101 lasted 2 hours without alerting — it was detected by a user reporting slowness.

## Current impact of the gap

<!-- PSPEC:REQUIRED Quantify the cost of not having this alert/dashboard/SLO. -->

- **Silent incidents**: 2 incidents in the last 3 months were not detected by alerts
- **Current MTTD**: 78 minutes (average) for latency degradation in `payment-gateway`
- **Expected MTTD with alert**: < 5 minutes

## Proposed solution

<!-- PSPEC:REQUIRED Describe what will be created/modified in observability. -->

**Example**: Create a `PaymentGatewayHighLatency` alert with a threshold of 500ms (warning) and 2000ms (critical) for p99 of successful requests. Use `histogram_quantile(0.99, ...)` over the existing `payment_request_duration_seconds` metrics.

## Change scope

<!-- PSPEC:REQUIRED Check all that apply. -->

- [ ] New alert created
- [ ] Existing alert modified (threshold, window, query)
- [ ] Existing alert removed
- [ ] New dashboard created
- [ ] Existing dashboard modified
- [ ] New SLO definition
- [ ] SLO target changed
- [ ] New recording rule
- [ ] Notification policy changed

## Alternatives considered

<!-- PSPEC:OPTIONAL -->

| Alternative | Reason discarded |
|-------------|-----------------|
| Alert on p50 (median) | Does not capture long tail; degradation can be invisible in the median |
| Fixed threshold at 1000ms | Too high — contractual SLO is 800ms |

## Required approvals

| Role | Name | Status |
|------|------|--------|
| SRE owner of the service | | Pending |
| On-call rotation lead | | Pending |
