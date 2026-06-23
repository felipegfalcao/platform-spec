---
schema: incident
incident-id: # INC-YYYY-NNN (same as postmortem)
postmortem-ref: # link or path to the postmortem
root-cause: # one sentence describing the root cause
author: # RCA author name
reviewer: # Tech Lead or EM who approves
date: # YYYY-MM-DD
status: # draft | review | approved
---

# RCA: [incident title]

<!-- PSPEC:REQUIRED The RCA deepens the postmortem analysis to identify the systemic root cause, not just the immediate trigger. A good RCA identifies a root cause that, if fixed, prevents not only this incident but an entire class of incidents. -->

> **Reference**: [Postmortem INC-YYYY-NNN](./postmortem.md)

---

## Root cause

<!-- PSPEC:REQUIRED One clear sentence. Describes the systemic problem, not the symptom. -->

**Root cause**: Absence of an operational impact validation gate for infrastructure configuration changes, allowing high-risk changes to be applied to production without review or a change window.

*Distinguish from the trigger event*:
- **Trigger event** (what triggered the incident): Change of `max_connections: 50 → 10` in the Redis ConfigMap
- **Root cause** (why the trigger could happen): Without a review gate, any engineer can modify critical configuration without impact analysis

---

## 5 Whys analysis

<!-- PSPEC:REQUIRED Use 5 Whys or Fishbone. Document EACH answer before asking the next "why". Stop when you reach a process or system that can be fixed. -->

**Problem**: Payment Gateway was unavailable for 45 minutes.

**Why 1**: Why was the Payment Gateway unavailable?
→ The Redis connection pool was exhausted, and the API returned `ECONNREFUSED` for all requests.

**Why 2**: Why did the connection pool exhaust?
→ Redis `max_connections` was reduced from 50 to 10, but the application continued opening up to 30 simultaneous connections at peak hours.

**Why 3**: Why was `max_connections` reduced without impact analysis?
→ The change was made by an engineer who believed they were reducing unnecessary connection overhead, not knowing the application uses up to 30 connections at peak.

**Why 4**: Why did the engineer not know the maximum connection usage?
→ There is no documentation of Redis connection behavior per service, and there is no gate that forces impact analysis before configuration changes.

**Why 5**: Why is there no impact analysis gate for ConfigMaps?
→ The PR review process for ConfigMaps is the same as for any other configuration change — no specific operational impact checklist.

**Root cause identified**: Absence of an operational validation gate for infrastructure configuration changes.

---

## Contributing factor analysis

<!-- PSPEC:REQUIRED Map each contributing factor from the postmortem to a corrective action or a conscious decision to accept the risk. No contributing factor should go unanswered. -->

| Contributing Factor | Type | Action Item |
|--------------------|------|-------------|
| Change without change window | Process gap | AT-001: Create change window checklist for ConfigMaps |
| No Redis config review gate | Tool/process gap | AT-002: Add Redis ConfigMap CI check |
| Alert with 5-min delay | Alert gap | AT-003: Create connection pool alert with for: 1m |
| Outdated runbook | Documentation gap | AT-004: Update Redis runbook with ConfigMap rollback |
| Deploy without validation window | Process gap | AT-001 (covers this case as well) |

---

## Action Items

<!-- PSPEC:REQUIRED Each action item must have: precise description, single owner, absolute deadline, and verifiable completion criterion. "Improve documentation" without owner and deadline is NOT a valid action item. -->

### AT-001 — Create mandatory checklist for infrastructure ConfigMap changes

- **Owner**: @sre-mary
- **Deadline**: 2024-03-22 (1 week after incident)
- **Priority**: P0 (prevents direct recurrence)
- **Completion criterion**: PR merged with PR template for ConfigMaps including "max_connections documented and validated" field

**Scope**: Create PR template at `.github/PULL_REQUEST_TEMPLATE/configmap_change.md` with checklist:
- [ ] Maximum connection/resource values documented in the design
- [ ] Production impact assessed (link to Platform Spec impact-analysis)
- [ ] Change window scheduled if blast radius ≥ medium

---

### AT-002 — Add Redis ConfigMap validation to CI

- **Owner**: @sre-peter
- **Deadline**: 2024-03-29 (2 weeks after incident)
- **Priority**: P1 (reduces recurrence risk)
- **Completion criterion**: CI pipeline blocks merge of ConfigMap with `max_connections < 20` without explicit SRE approval

**Scope**: Validation script in GitHub Actions that:
1. Detects changes in ConfigMaps with label `component=redis`
2. Validates that `max_connections >= 20` OR requires additional SRE approval
3. Adds a comment on the PR with automatic impact analysis

---

### AT-003 — Adjust connection pool alert to 1 minute

- **Owner**: @sre-john (on-call who experienced the incident)
- **Deadline**: 2024-03-18 (3 days after incident — urgent)
- **Priority**: P0 (improves immediate detection)
- **Completion criterion**: PrometheusRule updated with `for: 1m`, tested in staging, applied in production

**Note**: Create a Platform Spec change of type OBSERVABILITY for this change.

---

### AT-004 — Update Redis runbook with configuration rollback procedure

- **Owner**: @sre-mary
- **Deadline**: 2024-03-18 (3 days after incident)
- **Priority**: P0 (eliminates rollback delay in the next incident)
- **Completion criterion**: Runbook updated with ROLLBACK section covering ConfigMap rollback. Reviewed by at least 2 SREs who would respond to this type of incident.

**Note**: Create a Platform Spec change of type INCIDENT (runbook) for this item.

---

## Incident metrics

<!-- PSPEC:REQUIRED -->

| Metric | Value | Benchmark |
|--------|-------|-----------|
| MTTD (Mean Time to Detect) | 36 min | Target: < 5 min |
| MTTR (Mean Time to Respond) | 3 min | Target: < 5 min ✅ |
| MTTRS (Mean Time to Resolve) | 45 min | Target: < 30 min |
| Error budget consumed | 86.8% of monthly | Critical |

---

## Approval

| Role | Name | Status | Date |
|------|------|--------|------|
| Tech Lead | | Pending | |
| Engineering Manager | | Pending | |
| SRE Lead | | Pending | |

---

## Action item tracking

<!-- Update as action items are completed -->

| ID | Owner | Deadline | Status |
|----|-------|----------|--------|
| AT-001 | @sre-mary | 2024-03-22 | ⬜ pending |
| AT-002 | @sre-peter | 2024-03-29 | ⬜ pending |
| AT-003 | @sre-john | 2024-03-18 | ⬜ pending |
| AT-004 | @sre-mary | 2024-03-18 | ⬜ pending |
