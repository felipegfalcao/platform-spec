# Observability Change Validation Checklist

---

## Pre-flight

### Artifact completeness

- [ ] `proposal.md` — approved by SRE owner and on-call rotation lead
- [ ] `impact-analysis.md` — noise ratio analysis complete with historical data
- [ ] `design.md` — PromQL validated in staging Prometheus
- [ ] `runbook.md` — silence configured, rollback steps ready
- [ ] `tasks.md` — staging validation before prod apply

### PromQL validation gates

- [ ] Query executed in staging Prometheus — returns numeric values (not `[]` or `NaN`)
- [ ] Cardinality check passed: `count(<metric>)` is within acceptable range (< 10,000 series)
- [ ] Query does not use high-cardinality labels (user IDs, request IDs, pod names without aggregation)
- [ ] `for:` duration is appropriate — warning ≥ 5m, critical ≥ 2m (to prevent flapping)
- [ ] Thresholds justified with historical data (not arbitrary round numbers)

### Threshold justification

- [ ] Warning threshold: analyzed with `count_over_time(<expr>[30d])` — would have fired N times in 30 days
- [ ] Critical threshold: each firing in last 30 days would have been an actionable incident
- [ ] False positive rate estimated: < 5% of pages are expected to be false positives

### Dashboard (if applicable)

- [ ] Dashboard JSON exported and committed to `monitoring-repo/dashboards/`
- [ ] Dashboard UID is unique and follows naming convention
- [ ] All panels have thresholds matching alert thresholds (visual consistency)

---

## Staging validation

- [ ] PrometheusRule applied to staging namespace
- [ ] Alert state is `inactive` after 2 minutes (not immediately firing)
- [ ] Alert state is `ok` health (not `error` or `unknown`)
- [ ] Routing verified with `amtool config routes test`

---

## Production gates

- [ ] Staging validation complete
- [ ] Silence configured for 30 minutes post-deploy
- [ ] PrometheusRule applied to all production clusters
- [ ] Alert state `inactive` + `ok` confirmed in all clusters

---

## Post-apply verification

- [ ] Silence removed after 30-minute validation period
- [ ] No false positive firings in first 2 hours
- [ ] Alert documented in team runbook inventory
- [ ] Dashboard (if new) shared with team

---

## Rollback triggers

```
Alert fires immediately after deploy without real degradation?   → ROLLBACK (delete PrometheusRule)
Alert state shows "error" or "unknown"?                         → ROLLBACK (fix PromQL first)
Cardinality explosion (Prometheus memory spike)?                → ROLLBACK immediately
Alert generates > 5 pages/hour with no real incidents?          → ROLLBACK, recalibrate thresholds
```
