---
schema: observability
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# Observability Runbook: [change title]

**Estimated total duration**: `~20 minutes`
**Rollback window**: `5 minutes`

---

## PRE-APPLY

### P1 — Validate PromQL query in staging

```bash
# Via curl against the staging Prometheus API
curl -s 'http://prometheus-staging.internal/api/v1/query' \
  --data-urlencode 'query=histogram_quantile(0.99, sum by (le, service) (rate(payment_request_duration_seconds_bucket{service="payment-gateway", status=~"2.."}[5m])))' \
  | jq '.data.result'
# Expected: array with numeric values, not empty
```

**STOP if**: Query returns `[]` (no data) or `NaN` — the metric may not exist.

### P2 — Verify series cardinality

```bash
curl -s 'http://prometheus-staging.internal/api/v1/query' \
  --data-urlencode 'query=count(payment_request_duration_seconds_bucket{service="payment-gateway"})' \
  | jq '.data.result[0].value[1]'
# Expected: a reasonable number of series (< 10,000 to avoid cardinality explosion)
```

### P3 — Validate YAML with amtool

```bash
amtool check-config /path/to/alertmanager.yaml
# Expected: "Checking '/path/to/alertmanager.yaml'  SUCCESS"

# Validate the PrometheusRule
promtool check rules alerts/payment-gateway/latency.yaml
# Expected: "Checking alerts/payment-gateway/latency.yaml SUCCESS"
```

### P4 — Configure silence for the validation window

```bash
# Create a 30-minute silence to avoid a false pager during deploy
amtool silence add \
  alertname="PaymentGatewayHighLatency" \
  --comment="Platform Spec deploy — validating new alert rule" \
  --duration=30m \
  --alertmanager.url=http://alertmanager.internal
# Save the returned silence ID for possible early removal
```

---

## APPLY

### A1 — Apply in staging

```bash
# Via kubectl apply (Prometheus Operator)
kubectl apply -f alerts/payment-gateway/latency.yaml -n monitoring

# Verify the rule was loaded
kubectl get prometheusrule payment-gateway-latency -n monitoring
# Expected: recent AGE

# Wait for Prometheus to reload the rules (up to 1 minute)
sleep 60
```

### A2 — Verify the alert is in "inactive" state (not firing falsely)

```bash
# Check in Prometheus via API
curl -s 'http://prometheus.internal/api/v1/rules' \
  | jq '.data.groups[].rules[] | select(.name == "PaymentGatewayHighLatency") | {state, health}'
# Expected: {"state": "inactive", "health": "ok"}
# "inactive" means: rule loaded, threshold not reached — correct behavior
```

### A3 — Apply in production (if staging validated)

```bash
kubectl apply -f alerts/payment-gateway/latency.yaml -n monitoring --context prod-us-east-1
kubectl apply -f alerts/payment-gateway/latency.yaml -n monitoring --context prod-eu-west-1
```

---

## VERIFY

### V1 — Rule loaded and healthy

```bash
for CTX in prod-us-east-1 prod-eu-west-1; do
  echo "=== $CTX ==="
  kubectl --context=$CTX get prometheusrule payment-gateway-latency -n monitoring \
    -o jsonpath='{.metadata.name}{"\t"}{.metadata.creationTimestamp}{"\n"}'
done
```

**Success criterion**: Rule exists in both clusters with a recent timestamp.

### V2 — Alert in "inactive" state (not false-positive)

```bash
curl -s 'http://prometheus-prod.internal/api/v1/rules' \
  | jq '[.data.groups[].rules[] | select(.name | startswith("PaymentGateway")) | {name, state, health}]'
```

**Success criterion**: `state: "inactive"` and `health: "ok"` for both new alerts.

### V3 — Correct notification routing

```bash
# Verify routing without firing an alert (dry-run via amtool)
amtool config routes test \
  --alertmanager.url=http://alertmanager.internal \
  alertname=PaymentGatewayHighLatency \
  team=payment \
  severity=critical
# Expected: receiver payment-team-pagerduty
```

### V4 — Remove silence after validation

```bash
amtool silence expire <SILENCE_ID>
# Confirm removal
amtool silence query alertname=PaymentGatewayHighLatency
# Expected: no active silence
```

---

## ROLLBACK

### When to roll back an alert

- Alert fires immediately after deploy without real degradation
- Query is consuming excessive memory in Prometheus (> 500MB per query)
- Alert in `error` or `unknown` state in Prometheus

### R1 — Delete the PrometheusRule

```bash
kubectl delete prometheusrule payment-gateway-latency -n monitoring --context prod-us-east-1
kubectl delete prometheusrule payment-gateway-latency -n monitoring --context prod-eu-west-1
kubectl delete prometheusrule payment-gateway-latency -n monitoring --context staging
```

### R2 — If modifying an existing alert (restore previous version)

```bash
# Identify previous version in git
git log --oneline alerts/payment-gateway/latency.yaml

# Restore
git checkout <PREVIOUS_SHA> -- alerts/payment-gateway/latency.yaml
kubectl apply -f alerts/payment-gateway/latency.yaml -n monitoring
```

### R3 — Verify post-rollback

```bash
curl -s 'http://prometheus-prod.internal/api/v1/rules' \
  | jq '[.data.groups[].rules[] | select(.name | startswith("PaymentGateway"))]'
# Expected: rule removed OR previous version restored
```
