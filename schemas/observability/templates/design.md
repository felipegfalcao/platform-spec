---
schema: observability
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# Observability Design: [change title]

## 1. PromQL query — mandatory validation

<!-- PSPEC:REQUIRED The query must be validated in staging or in the Prometheus Explorer before creating the alert. Paste the validation result. -->

### 1.1 Base query

```promql
# Query for p99 latency of successful payment-gateway requests
histogram_quantile(
  0.99,
  sum by (le, service) (
    rate(payment_request_duration_seconds_bucket{
      service="payment-gateway",
      status=~"2.."
    }[5m])
  )
)
```

**Validation in staging**:

- [ ] Query executed in the staging Prometheus
- [ ] Returns numeric values (not `NaN` or `no data`)
- [ ] Value range is reasonable: `[0.05, 0.8]` seconds under normal conditions
- [ ] Series cardinality: `N series` — acceptable (limit: < 10,000)

### 1.2 Recording rule query (if applicable)

<!-- PSPEC:OPTIONAL If the query is computationally expensive, create a recording rule first. -->

```yaml
# recording rule to pre-compute and reduce cost
- record: payment:request_duration_seconds:p99:rate5m
  expr: |
    histogram_quantile(
      0.99,
      sum by (le, service) (
        rate(payment_request_duration_seconds_bucket{status=~"2.."}[5m])
      )
    )
```

## 2. Alert configuration

<!-- PSPEC:REQUIRED Complete YAML ready to apply. -->

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: payment-gateway-latency
  namespace: monitoring
  labels:
    # Labels for the Prometheus Operator to select this rule
    prometheus: kube-prometheus
    role: alert-rules
    team: payment
spec:
  groups:
    - name: payment-gateway.latency
      interval: 30s  # evaluation frequency
      rules:
        - alert: PaymentGatewayHighLatency
          expr: |
            histogram_quantile(
              0.99,
              sum by (le, service) (
                rate(payment_request_duration_seconds_bucket{
                  service="payment-gateway",
                  status=~"2.."
                }[5m])
              )
            ) > 0.5
          for: 5m  # must maintain threshold for 5 minutes before firing
          labels:
            severity: warning
            team: payment
            service: payment-gateway
            # Label for SLO tracking
            slo: payment-gateway-latency
          annotations:
            summary: "Payment Gateway p99 latency above 500ms"
            description: >
              Payment Gateway p99 latency is {{ $value | humanizeDuration }} for
              service {{ $labels.service }}. SLO threshold is 800ms.
            runbook_url: "https://wiki.internal/runbooks/payment-gateway-latency"
            dashboard_url: "https://grafana.internal/d/payment-gateway"

        - alert: PaymentGatewayCriticalLatency
          expr: |
            histogram_quantile(
              0.99,
              sum by (le, service) (
                rate(payment_request_duration_seconds_bucket{
                  service="payment-gateway",
                  status=~"2.."
                }[5m])
              )
            ) > 2.0
          for: 2m  # critical fires faster
          labels:
            severity: critical
            team: payment
            service: payment-gateway
            slo: payment-gateway-latency
          annotations:
            summary: "CRITICAL: Payment Gateway p99 latency above 2s — SLO breach imminent"
            description: >
              Payment Gateway p99 latency is {{ $value | humanizeDuration }}.
              SLO breach will occur in approximately {{ ... }} minutes at current rate.
            runbook_url: "https://wiki.internal/runbooks/payment-gateway-latency"
```

## 3. Threshold justification

<!-- PSPEC:REQUIRED Thresholds without data-backed justification are rejected in review. -->

| Threshold | Value | Justification |
|-----------|-------|---------------|
| Warning | 500ms | 62.5% of the contractual SLO of 800ms. Margin to act before breach. |
| Critical | 2000ms | 2.5x the SLO. If p99 > 2s, the SLO is already in breach for tail requests. |
| `for: 5m` (warning) | 5 minutes | Eliminates transient spikes. Historical data: spikes > 5min = real degradation. |
| `for: 2m` (critical) | 2 minutes | Faster response in critical scenario, still filters 1–2 min spikes. |

## 4. Location in the repository

```text
monitoring-repo/
└── alerts/
    └── payment-gateway/
        └── latency.yaml    ← file to be created
```

## 5. Grafana dashboard (if applicable)

<!-- PSPEC:OPTIONAL If the change includes a dashboard, the JSON must be versioned in the repository. -->

```json
{
  "uid": "payment-gateway-latency",
  "title": "Payment Gateway — Latency",
  "panels": [
    {
      "title": "p99 Latency",
      "type": "timeseries",
      "targets": [
        {
          "expr": "histogram_quantile(0.99, sum by (le) (rate(payment_request_duration_seconds_bucket{service='payment-gateway', status=~'2..'}[5m])))",
          "legendFormat": "p99"
        }
      ],
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 0.5},
          {"color": "red", "value": 2.0}
        ]
      }
    }
  ]
}
```

## 6. Notification policy

<!-- PSPEC:REQUIRED Confirm the alert will be routed correctly without creating a new routing rule. -->

**Existing routing** (in `alertmanager.yaml`):

```yaml
- match:
    team: payment
  receiver: payment-team-slack
  routes:
    - match:
        severity: critical
      receiver: payment-team-pagerduty
```

**The new alert has `team: payment`** — it will be routed automatically to:

- `warning` → Slack `#alerts-payment`
- `critical` → PagerDuty, `payment-oncall` rotation

**No changes to the notification policy required.**
