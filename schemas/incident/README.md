# Incident Schema

Schema for incident documentation. The flow is inverted compared to other schemas: **learn first**, then document the procedure.

## When to use this schema

Use `incident` when:

- A production incident has been resolved and requires a postmortem
- A service degradation paged on-call
- A formal RCA was requested
- An operational runbook needs to be created or updated
- The incident consumed > 20% of the monthly error budget

## Sequence

```text
postmortem → rca → runbook
```

The runbook is **optional** — it is only created when the incident results in a new or updated operational procedure.

## Blameless principle

Postmortems in this framework are blameless. The focus is on systems and processes, not on individuals. The timeline uses objective data (logs, metrics, alerts). Avoid phrases like "engineer X forgot to..." — prefer "the review process did not detect...".

## Templates

| Template | When to create | Deadline |
|----------|---------------|----------|
| [postmortem.md](templates/postmortem.md) | Every P1 or P2 incident | Within 24h of resolution |
| [rca.md](templates/rca.md) | After postmortem is approved | Within 72h of resolution |
| [runbook.md](templates/runbook.md) | When the incident reveals a runbook gap | Within 1 week |

## Required context

Read [`context/rollback-patterns.md`](../../context/rollback-patterns.md) to understand the rollback patterns used during the incident — this feeds the action items in the RCA.
