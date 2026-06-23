# Context: SLO Error Budget — Calculation and Change Management

> Read this file before creating any observability schema artifact or assessing SLO impact in any schema's impact-analysis.

---

## 1. Core concepts

### Error budget

The error budget is the maximum amount of downtime or errors a service can experience while still meeting its SLO target.

```
Error budget = (1 - SLO target) × period duration

Example: 99.9% availability SLO over 30 days
Error budget = (1 - 0.999) × 30 × 24 × 60 = 43.8 minutes/month
```

### Burn rate

The burn rate measures how fast the error budget is being consumed relative to the allowed rate.

```
Burn rate = (error rate observed) / (1 - SLO target)

Example: If your SLO is 99.9% and you're seeing 1% error rate:
Burn rate = 0.01 / 0.001 = 10x
→ You're consuming budget 10× faster than allowed
→ At this rate, budget runs out in 30/10 = 3 days
```

---

## 2. How to calculate change impact

Before filling in the `slo-impact` field in any impact-analysis, calculate the worst-case scenario duration and convert to budget percentage.

### Formula

```
Impact % = (estimated outage duration in minutes) / (monthly error budget in minutes) × 100

Example: 5-minute potential outage, 99.9% SLO
Monthly budget = 43.8 min
Impact = 5 / 43.8 × 100 = 11.4%
→ slo-impact: 0.01-0.1% is WRONG here — classify as >0.1%
```

### Impact classification table

| Classification | Budget consumed | Example scenario |
|---------------|-----------------|-----------------|
| `none` | 0% | Adding a new alert rule (no service change) |
| `<0.01%` | < 0.01% | < 26 seconds of potential outage (99.9% SLO) |
| `0.01-0.1%` | 0.01% to 0.1% | 26 seconds to 4.4 minutes of potential outage |
| `>0.1%` | > 0.1% | > 4.4 minutes of potential outage |

**Note**: Always use the **worst-case scenario** duration, not the expected duration.

---

## 3. Multi-window burn rate alerts (Google SRE model)

Use multi-window burn rate alerts to detect budget exhaustion at different time horizons.

### Recommended alert windows

| Burn rate | Alert window | Good for | Action |
|-----------|-------------|----------|--------|
| 14.4× | 1 hour | Fast critical failures | Page immediately |
| 6× | 6 hours | Significant degradation | Page — investigate now |
| 3× | 1 day | Slow burn | Ticket — fix this sprint |
| 1× | 3 days | Budget leak | Review — trending badly |

### PromQL for multi-window burn rate alerts

```promql
# Critical: budget exhausted in < 2 hours (14.4× burn rate over 1h)
(
  (1 - (
    sum(rate(http_requests_total{status!~"5.."}[1h]))
    /
    sum(rate(http_requests_total[1h]))
  )) / (1 - 0.999)
) > 14.4

# Warning: budget exhausted in < 5 days (6× burn rate over 6h)
(
  (1 - (
    sum(rate(http_requests_total{status!~"5.."}[6h]))
    /
    sum(rate(http_requests_total[6h]))
  )) / (1 - 0.999)
) > 6
```

---

## 4. Change window thresholds

### When a change requires a formal change window

| Condition | Required action |
|-----------|----------------|
| Blast radius `medium` | Scheduled change window (team notified, on-call aware) |
| Blast radius `high` | Formal change window + SRE Lead approval |
| Blast radius `critical` | Formal change window + SRE Lead + Engineering Manager |
| SLO impact `>0.1%` | Budget approval from SRE Lead regardless of blast radius |
| Error budget remaining < 20% | All changes require SRE Lead approval |
| Error budget remaining < 10% | **Change freeze** — only critical fixes with EM approval |

### Error budget remaining calculation

```bash
# Example with Sloth (Prometheus-based SLO tool)
kubectl get slo <slo-name> -n monitoring \
  -o jsonpath='{.status.errorBudgetRemaining}'

# Manual calculation from Prometheus
# Remaining budget in minutes (for a 30-day window, 99.9% SLO):
(
  sum_over_time(slo_error_budget_remaining[30d])
  / count_over_time(slo_error_budget_remaining[30d])
) * 43.8  # = minutes remaining
```

---

## 5. Change freeze rules

### Automatic freeze triggers

A change freeze is declared automatically when:
- Error budget remaining drops below 10% in any rolling 30-day window
- An active P1 or P2 incident is in progress
- During pre-declared freeze windows (e.g., Black Friday week, end of quarter)

### During freeze: what is allowed

| Allowed during freeze | Requires approval |
|----------------------|-------------------|
| Security hotfixes (CVE) | SRE Lead |
| Bug fixes causing active P1/P2 | Incident Commander |
| Rollback of a previous change | SRE Lead |
| Observability-only changes (alerts, dashboards) | SRE Lead |

| Blocked during freeze | No exceptions |
|----------------------|---------------|
| Feature deployments | Absolute block |
| Infrastructure scaling (non-emergency) | Absolute block |
| Dependency upgrades | Absolute block |
| New ApplicationSet creation | Absolute block |

---

## 6. Impact calculation by change type

### GitOps changes

```
Worst-case impact = time to detect sync failure + time to execute rollback

Typical rollback time for GitOps: 2-5 minutes (git revert + ArgoCD sync)
Detection time: ArgoCD reconciliation interval (default: 3 minutes)

Conservative estimate: 8 minutes worst-case
Budget impact (99.9% SLO): 8 / 43.8 × 100 = 18.3% → classify as >0.1%
```

### IAC changes (in-place modification)

```
Worst-case impact = time for AWS resource modification + detection time

Examples:
- RDS storage type change: 15-30 minutes of I/O degradation
- Security group rule: near-instantaneous
- EC2 instance type: requires stop/start = 5-10 min downtime

RDS modification: 20 min / 43.8 min = 45.7% → critical, requires budget approval
```

### Observability changes

```
Typically slo-impact: none
Exception: removing a critical alert that is actively preventing a worse incident
```

---

## 7. Rolling vs. calendar budget windows

### Rolling 30-day window (recommended)

The error budget is calculated over the last 30 days from now. This means:
- An incident from 29 days ago still counts against your budget today
- The budget "recovers" gradually as old incidents fall out of the window
- More representative of recent reliability

### Calendar monthly window

Budget resets on the 1st of each month. Common in contractual SLAs but less useful for operational decisions — a team can spend most of their budget on the 2nd of the month and feel no pressure until the next month.

**This framework uses rolling 30-day windows** for operational change decisions.

---

## 8. Glossary

| Term | Definition |
|------|-----------|
| **SLO** | Service Level Objective — a target reliability metric (e.g., 99.9% availability) |
| **SLA** | Service Level Agreement — contractual commitment, typically to external customers |
| **Error budget** | The allowed amount of unreliability: `(1 - SLO target) × period` |
| **Burn rate** | How fast the error budget is being consumed vs. the allowed rate |
| **Burn rate alert** | Alert that fires when budget will be exhausted within a certain window |
| **Change freeze** | Period during which only critical changes are allowed |
| **Rolling window** | Budget calculated over the last N days, not a calendar period |
