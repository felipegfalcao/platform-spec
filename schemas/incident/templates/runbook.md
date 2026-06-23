---
schema: incident
incident-id: # INC-YYYY-NNN that originated this runbook
rca-ref: # path to the RCA that generated this runbook
runbook-type: # response | recovery | rollback
services-covered: # list of services
author: # author name
reviewer: # at least 2 SREs from the rotation
date: # YYYY-MM-DD
status: # draft | review | approved
---

# Operational Runbook: [procedure title]

<!-- PSPEC:REQUIRED Runbooks created via the INCIDENT schema are operational procedures derived from real incidents. Unlike apply runbooks (GitOps/IAC), this runbook is about RESPONDING to a production problem. -->

> **Origin**: [INC-YYYY-NNN](./postmortem.md) — [RCA](./rca.md)
> **Last updated**: YYYY-MM-DD

---

## What this runbook covers

<!-- PSPEC:REQUIRED Describe the exact scenario this runbook resolves. Be specific — "Redis issues" is too vague; "Redis connection pool exhausted causing API unavailability" is precise. -->

**Scenario**: Redis connection pool exhausted, causing `ECONNREFUSED` on all API requests.

**Typical symptoms**:
- Alert `RedisConnectionPoolExhausted` fired
- 100% error rate on the affected endpoint
- API logs with `Error: connect ECONNREFUSED` or `maxRetriesPerRequest exceeded`
- `redis-cli INFO clients` shows `connected_clients` = `maxclients`

**Do NOT use this runbook for**:
- Redis with high latency but no pool exhaustion → see `runbook-redis-performance.md`
- Redis with corrupted data → see `runbook-redis-data-recovery.md`
- Total Redis instance failure → see `runbook-redis-failover.md`

---

## Quick diagnosis (< 2 minutes)

<!-- PSPEC:REQUIRED Sequence to confirm the diagnosis before executing any action. -->

```bash
# 1. Confirm pool exhaustion
redis-cli -h redis.internal INFO clients | grep connected_clients
# Exhausted if: connected_clients == maxclients

# 2. Confirm what maxclients is configured to
redis-cli -h redis.internal CONFIG GET maxclients
# Suspicious if very low (< 20 for high-concurrency services)

# 3. Verify who is using the connections
redis-cli -h redis.internal CLIENT LIST | wc -l
redis-cli -h redis.internal CLIENT LIST | awk '{print $2}' | sort | uniq -c | sort -rn | head -10
# Identify the service with the most open connections
```

---

## IMMEDIATE RESPONSE (first 5 minutes)

### R1 — Escalate and communicate

```bash
# Post in #incident
"🔴 INCIDENT: Redis connection pool exhausted - [service] unavailable.
 IC: @your-name. Diagnosis in progress.
 Dashboard: https://grafana.internal/d/redis"

# Create incident channel if impact > 1 service
/incident create "Redis pool exhausted affecting [service]"
```

### R2 — Temporary relief (buys time for diagnosis)

```bash
# OPTION A: Temporarily increase maxclients (revert after diagnosis)
redis-cli -h redis.internal CONFIG SET maxclients 200
# WARNING: This increases memory usage. Check available RAM first.
redis-cli -h redis.internal INFO memory | grep used_memory_human

# OPTION B: Kill idle connections from a specific service
# Identify CLIENT ID of the causing service:
redis-cli -h redis.internal CLIENT LIST | grep "name=api-backend"
# Kill idle connections (IDLE > 60s):
redis-cli -h redis.internal CLIENT KILL IDLE 60
```

---

## ROOT CAUSE — checks

### C1 — Recent configuration change?

```bash
# Check if there was a Redis ConfigMap change in the last 60 minutes
kubectl get events -n redis --field-selector reason=Killing --sort-by='.lastTimestamp' | head -5
kubectl rollout history configmap redis-config -n redis
git log --oneline --since="2 hours ago" -- k8s/redis/
```

**If yes → execute CONFIGURATION ROLLBACK below.**

### C2 — Unexpected load increase?

```bash
# Check if the number of application pods increased
kubectl get pods -n api --show-labels | grep -c Running

# Check for retry storm (pods attempting to reconnect in a loop)
kubectl logs -n api deployment/api-backend --tail=100 | grep -c "ECONNREFUSED"
# If > 50 messages in 100 lines → retry storm in progress
```

**If retry storm → temporary scale down to break the cycle:**
```bash
kubectl scale deployment api-backend -n api --replicas=5  # reduce from N to 5
# Wait for connections to stabilize
# Gradually scale back up after pool recovers
```

---

## CONFIGURATION ROLLBACK

<!-- PSPEC:REQUIRED Use when the cause is a recent configuration change. -->

```bash
# 1. Identify the current ConfigMap
kubectl get configmap redis-config -n redis -o yaml > /tmp/redis-config-current.yaml

# 2. Check previous version
kubectl rollout history configmap redis-config -n redis
# OR check in git:
git log -p k8s/redis/configmap.yaml | head -50

# 3. Restore previous version via git revert
git revert <SHA-OF-CHANGE> --no-edit
git push origin main

# 4. Apply directly if git revert is too slow
kubectl apply -f k8s/redis/configmap.yaml
kubectl rollout restart deployment redis -n redis  # if ConfigMap is not hot-reloadable
```

**Verify after rollback**:
```bash
watch -n 5 'redis-cli -h redis.internal INFO clients | grep connected_clients'
# Wait for connected_clients < maxclients
```

---

## POST-RESOLUTION VERIFY

```bash
# 1. Error rate back to 0%
curl -s http://api.internal/health | jq '.status'
# Expected: "ok"

# 2. Redis accepts new connections
redis-cli -h redis.internal PING
# Expected: PONG

# 3. Pool with sufficient headroom
redis-cli -h redis.internal INFO clients
# Verify: connected_clients < maxclients * 0.8

# 4. No active related alerts
amtool alert query alertname="RedisConnectionPoolExhausted"
# Expected: no alerts
```

---

## RESOLUTION COMMUNICATION

```
#incident: "✅ RESOLVED: Redis pool exhausted in [service] resolved at HH:MM UTC.
 Cause: [configuration X / load spike Y].
 Action taken: [ConfigMap rollback / scale down / maxclients increased].
 Impact: [N minutes of unavailability].
 Postmortem: [link] will be published within 24h."
```

---

## Mandatory post-incident

1. [ ] Revert any temporary changes (e.g., maxclients increased for relief)
2. [ ] Open postmortem (template: `schemas/incident/templates/postmortem.md`)
3. [ ] Document anything that differed from this runbook in the feedback section below

---

## Usage history and feedback

<!-- PSPEC:OPTIONAL Update each time this runbook is used in a real incident. -->

| Incident | Date | Worked? | What was wrong in the runbook |
|----------|------|---------|-------------------------------|
| INC-2024-101 | 2024-03-15 | Partially | Missing ConfigMap rollback section |
| | | | |
