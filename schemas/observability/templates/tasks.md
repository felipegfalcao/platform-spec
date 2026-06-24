---
schema: observability
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# Observability Tasks: [change title]

**Runbook approved by**: `@name` on `YYYY-MM-DD`
**Executor**: `@name`

---

## T1 — Validate PromQL query in staging

- **Owner**: @sre
- **Estimate**: 15 minutes

```bash
curl -s 'http://prometheus-staging.internal/api/v1/query' \
  --data-urlencode 'query=histogram_quantile(0.99, ...)' | jq '.data.result'
```

- [ ] Query returns valid values (not `[]` or `NaN`)
- [ ] Cardinality within limit (< 10,000 series)
- [ ] Completed

---

## T2 — Create PrometheusRule and apply in staging

- **Owner**: @sre
- **Estimate**: 10 minutes

```bash
kubectl apply -f alerts/payment-gateway/latency.yaml -n monitoring
sleep 60
kubectl get prometheusrule payment-gateway-latency -n monitoring
```

- [ ] Rule applied in staging
- [ ] `inactive` state confirmed (not firing falsely)
- [ ] Completed

---

## T3 — Apply in production

- **Owner**: @sre
- **Estimate**: 5 minutes

```bash
for CTX in prod-us-east-1 prod-eu-west-1; do
  kubectl apply -f alerts/payment-gateway/latency.yaml -n monitoring --context=$CTX
done
```

- [ ] Applied in prod-us-east-1
- [ ] Applied in prod-eu-west-1
- [ ] `inactive` state in both clusters
- [ ] Notification routing validated via amtool
- [ ] Silence removed after validation
- [ ] Completed

---

## T4 — Document and communicate

- **Owner**: @sre

```text
#alerts-payment: "New alert PaymentGatewayHighLatency is active.
Warning: p99 > 500ms for 5min. Critical: p99 > 2s for 2min.
Runbook: <link>"
```

- [ ] Team notified
- [ ] Alert added to the team's alert inventory
- [ ] Completed
