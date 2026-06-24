---
schema: incident
incident-id: # INC-YYYY-NNN
severity: # P1 | P2 | P3
duration: # HH:MM (time between detection and resolution)
services-affected: # list of services
error-budget-consumed: # percentage of monthly budget
author: # incident commander name
date: # YYYY-MM-DD (date of the incident, not of writing)
status: # draft | review | approved
---

# Postmortem: [descriptive incident title]

<!-- PSPEC:REQUIRED Title must describe the symptom, not the cause. Example: "Payment Gateway Unavailable 45min" not "Redis bug caused outage". The cause is analyzed in the RCA. -->

> **This document is blameless.** The goal is to learn, not to assign blame.
> Focus on systems and processes, never on individuals.

---

## Executive summary

<!-- PSPEC:REQUIRED 3–5 sentences for non-technical stakeholders. What happened, when, for how long, and what was the business impact. -->

**Example**: On 03/15/2024 at 2:23 PM UTC, the payment service was unavailable for 45 minutes to 100% of users. The issue was caused by connection pool exhaustion in Redis after an unplanned configuration change. Approximately 12,000 payment transactions were affected, with an estimated unprocessed revenue of $280,000. Service was restored at 3:08 PM UTC after rolling back the configuration.

---

## Impact

<!-- PSPEC:REQUIRED Impact must be measured, not vaguely estimated. Use metrics, logs, and analytics data. -->

| Metric | Value |
|--------|-------|
| Total duration (detection → resolution) | 45 minutes |
| Total unavailability duration | 38 minutes |
| Affected users | ~45,000 (100% of active users) |
| Lost transactions | ~12,000 |
| Unprocessed revenue | ~$280,000 |
| Error budget consumed | 38/43.8 min = **86.8% of monthly budget** |
| Affected SLO | Payment Availability (target: 99.9%) |
| SLO status after incident | **Breach** — 98.8% for the month |

---

## Timeline

<!-- PSPEC:REQUIRED Use timestamps with timezone. Each entry must have a source (alert, log, Slack, PagerDuty). Build the timeline from data before analyzing it. -->

| Time (UTC) | Event | Source |
|-----------|-------|--------|
| 13:47 | Redis configuration deployed (`max_connections: 50 → 10`) to production | Deploy log |
| 14:23 | Alert `RedisConnectionPoolExhausted` fires | PagerDuty #INC-001 |
| 14:25 | On-call (@sre-john) paged via PagerDuty | PD timeline |
| 14:28 | On-call confirms `ECONNREFUSED` errors in API logs | Datadog |
| 14:35 | First diagnosis: 100% error rate on `/api/payments` | Grafana |
| 14:42 | Redis suspicion confirmed: `redis-cli INFO clients` shows `connected_clients: 10/10` | SSH prod |
| 14:50 | Redis restart attempted (fails — does not resolve) | old runbook |
| 14:58 | SRE Lead (@sre-mary) joins the call | Slack #incident |
| 15:02 | Config deploy from 13:47 identified as cause | Deploy log |
| 15:06 | Redis ConfigMap rollback started | kubectl apply |
| 15:08 | Service restored — error rate back to 0% | Grafana |
| 15:35 | Incident declared resolved | PD |

---

## Detection and response

<!-- PSPEC:REQUIRED Assess the quality of detection and response. -->

**How it was detected**: Automatic alert `RedisConnectionPoolExhausted` (previously configured).

**Time between failure and detection**: 36 minutes (deploy at 13:47, alert at 14:23).

**Why detection was slow**: The connection pool alert only fires after 5 minutes of exhaustion. The deploy was made during a low-traffic period — load increased gradually until the pool was exhausted at 14:23.

**What worked well**:

- Automatic alert detected and paged correctly
- On-call responded in < 3 minutes
- #incident channel created quickly with the right stakeholders

**What did not work well**:

- Rollback took 6 extra minutes due to lack of a runbook for Redis configuration
- Config deploy had no change window or blast radius review
- Available runbook covered Redis restart, not configuration rollback

---

## Contributing factors

<!-- PSPEC:REQUIRED List ALL factors that contributed to the incident. Do not confuse contributing factors with root cause — the RCA identifies the root cause. -->

1. **Configuration change without change window**: `max_connections` was changed from 50 to 10 without impact analysis or an approved change window
2. **No review gate for ConfigMap changes**: CI does not validate the impact of Redis configuration changes
3. **Alert with 5-minute delay**: The alert only fires after 5 continuous minutes — during low traffic, the pool took 36 minutes to exhaust
4. **Outdated runbook**: The Redis runbook covered only restart, with no configuration rollback procedure
5. **Deploy during low-traffic hours without post-deploy monitoring**: The change was applied and the engineer left without waiting for the validation window

---

## What worked well

<!-- PSPEC:REQUIRED Document what should be preserved and reinforced. -->

- Alert system detected the problem automatically
- On-call responded within SLA (< 5 minutes)
- Incident commander was designated quickly
- Communication with stakeholders was proactive and clear
- Rollback was technically straightforward once the cause was identified

---

## Evidence links

<!-- PSPEC:REQUIRED -->

- Grafana snapshot (incident period): [link]
- PagerDuty incident timeline: [link]
- Deploy log (13:47): [link]
- Slack thread #incident: [link]
- CloudWatch Logs during incident: [link]
