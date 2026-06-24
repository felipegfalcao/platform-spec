---
schema: observability
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# Observability Impact Analysis: [change title]

## 1. Alert coverage

### 1.1 Current state

| Service | Metric | Existing alert? | Gap |
|---------|--------|-----------------|-----|
| `payment-gateway` | Error rate | Yes — `PaymentGatewayHighErrorRate` | None |
| `payment-gateway` | p99 latency | **No** | No latency alert |
| `payment-gateway` | Throughput | No | Out of scope for this change |

### 1.2 State after the change

| Alert | Type | Severity | Action |
|-------|------|----------|--------|
| `PaymentGatewayHighLatency` | Created | warning + critical | New creation |

## 2. SLO impact of this change

<!-- PSPEC:REQUIRED Calculate using context/slo-budget.md -->

**Change type**: `additive` — only creates a new alert, does not modify existing ones.

**SLO impact**: `none` — alert creation does not affect service availability.

**Risk of alert storm during deploy**: Low — new alert with `for: 5m` before firing.

## 3. Noise ratio analysis

<!-- PSPEC:REQUIRED Validate the proposed threshold against historical data before creating the alert. -->

### 3.1 Historical data analysis

```promql
# Query to evaluate how many times the proposed threshold would have alerted in the last 30d
# Run in Prometheus/Grafana before creating the alert
sum(rate(payment_request_duration_seconds_bucket{le="0.5",status=~"2.."}[5m]))
  / sum(rate(payment_request_duration_seconds_count{status=~"2.."}[5m]))
```

**Results over the last 30 days**:

- Peaks above 500ms (warning): `N occurrences` — evaluate whether this is acceptable noise
- Peaks above 2000ms (critical): `N occurrences` — each one should have become a pager

**Threshold decision**:

- Warning 500ms: `X%` of the time alerting — acceptable / adjust to `Y ms`
- Critical 2000ms: `Z%` of the time alerting — represents real incidents

### 3.2 Estimated false positive rate

<!-- PSPEC:REQUIRED -->

**False positive**: alert fires but there is no real degradation for the user.

**Estimate**: Analyze historical data. Goal: < 5% of pages are false positives.

## 4. Impact on notification policy

<!-- PSPEC:REQUIRED If the change affects alert routing. -->

**Current routing**: All `payment-gateway` alerts go to `#alerts-payment` (Slack) and page the team via PagerDuty for `severity=critical`.

**Routing for the new alert**: Same pattern — `PaymentGatewayHighLatency` with label `team=payment` follows the existing matcher.

**Expected new noise**: ~2 warning alerts/month (based on historical data), ~0.5 critical pages/month.

## 5. Blast radius

**Blast radius**: `low`

**Justification**: Adding an alert does not affect the monitored service. The worst case is a poorly calibrated alert that generates noise in the on-call rotation. Rollback is simple: delete the `PrometheusRule`.

## 6. Change window

**Change window**: `none`

**Justification**: Adding an alert rule does not require a change window. The new alert has `for: 5m` to avoid firing immediately when loaded by Prometheus.

## 7. Rollback trigger

Execute alert rollback if:

- More than 5 `warning` fires in 1 hour without confirmed real degradation (false positive)
- Pager fired for `critical` when the service was healthy
- PromQL query causing high memory consumption in Prometheus (cardinality explosion)
