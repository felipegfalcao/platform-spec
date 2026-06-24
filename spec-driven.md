# Spec-Driven Development for Infrastructure

> Platform Spec is built on a practice called **Spec-Driven Development (SDD)**.
> This document explains what SDD is, why infrastructure changes need it, and how
> the framework enforces it.

---

## The problem SDD solves

Infrastructure changes fail in predictable ways. Not because engineers are careless,
but because the process around changes is informal.

The pattern repeats across teams:

1. Someone identifies a problem — a performance bottleneck, an alert gap, an outdated generator
2. They open a PR with the fix
3. The PR description says "fix: update RDS storage type"
4. Review happens on the diff, not on the reasoning
5. The change is merged and applied
6. Something breaks — or doesn't break, but nobody knows why it worked

The failure is not in the code. It is in what was never written down:

- Why was this the right solution, not the alternatives?
- What is the worst case if this goes wrong?
- What are the exact commands to roll back at 3am?
- Did we check error budget before scheduling this?

SDD forces these answers to exist **before** execution, not after.

---

## What Spec-Driven Development is

SDD is the practice of treating the **specification of a change** as the primary
artifact, with the implementation following from it.

In software development, a spec might be an RFC, a design doc, or a ticket with
acceptance criteria. In infrastructure, the equivalent is a sequence of artifacts
that capture the full lifecycle of a change:

```text
proposal → impact-analysis → design → runbook → tasks
```

Each artifact answers a specific question:

| Artifact | Question answered |
|----------|------------------|
| `proposal` | What problem are we solving and why now? |
| `impact-analysis` | What breaks if this goes wrong? How much of our error budget does this risk? |
| `design` | What exactly will change? Show the diff. |
| `runbook` | How do we execute and roll back safely? |
| `tasks` | Who does what, in what order, with what success criterion? |

The sequence is **inviolable**. You cannot write the design before the impact analysis.
You cannot execute tasks without a runbook. This is not bureaucracy — it is the minimum
structure that makes a change safe to hand off, review, and execute under pressure.

---

## Why infrastructure specifically

Application code has a feedback loop that infrastructure often lacks:

- A broken application returns an error immediately
- A broken Terraform apply might not surface for minutes — or until the next deploy
- A broken ArgoCD ApplicationSet might silently orphan resources for hours
- A miscalibrated alert might not fire until the next incident

Infrastructure changes also have higher blast radius. Deleting an S3 bucket affects
every service that writes to it. Enabling `prune: true` on an ApplicationSet in the
wrong moment deletes running workloads. Changing `max_connections` on Redis takes
down the API.

SDD exists because infrastructure changes require **thinking before acting** — and
thinking needs a structure to produce something reviewable.

---

## The four schemas

Platform Spec defines four schemas, each mapping to a class of infrastructure change:

### `gitops`

Changes to the declarative deployment plan managed by ArgoCD. The final artifact is
YAML committed to a GitOps repository. The risk is that ArgoCD reconciles immediately
after merge — there is no manual apply step to catch mistakes.

### `iac`

Changes to infrastructure provisioned via Terraform and Terragrunt. The final artifact
is HCL. The risk is that `terraform apply` can destroy resources, and rollback may
require a second destructive operation.

### `observability`

Changes to the alerting and SLO layer. The final artifact is a PrometheusRule, a
Grafana dashboard JSON, or an SLO definition. The risk is a miscalibrated alert that
either silences real incidents (false negative) or exhausts the on-call rotation
(false positive).

### `incident`

Documentation of incidents that occurred. The flow is inverted: the sequence is
`postmortem → rca → runbook`, because you learn first and document the procedure
after. No code or infrastructure is changed directly under this schema.

---

## The role of AI agents

Platform Spec is designed to be used with AI coding assistants and autonomous agents.
`AGENTS.md` is the entry point for any AI operating in this repository.

The framework makes AI contributions safe through structure:

- The artifact sequence forces an AI to produce an impact analysis before a design
- `PSPEC:REQUIRED` markers tell the AI which sections cannot be left empty
- Context files (`context/argocd.md`, `context/terragrunt.md`, etc.) give the AI
  the domain knowledge it needs to produce accurate content
- Validation gates give the AI explicit criteria for "done"

The result is that an AI agent following AGENTS.md produces changes with the same
structure and safety properties as a senior SRE — because the structure itself
encodes the senior SRE's reasoning process.

---

## What SDD is not

**SDD is not process for process's sake.** The artifacts exist to reduce mean time
to recovery, not to generate paperwork. A runbook that saves 6 minutes during a 45-minute
outage justifies the 20 minutes it took to write.

**SDD is not a replacement for GitOps or IaC.** It is a layer on top of them. The final
artifact of a GitOps change is still YAML committed to a repo and reconciled by ArgoCD.
SDD specifies the process around that commit, not the commit itself.

**SDD is not sequential waterfall.** Artifacts can evolve as you learn. A proposal that
reveals a higher blast radius during impact analysis should be revised, not discarded.
The sequence enforces order of reasoning, not order of calendar events.

---

## How to start

If you are new to Platform Spec:

1. Read [`AGENTS.md`](AGENTS.md) — even if you are not an AI agent, this is the clearest
   description of how the framework classifies changes
2. Read the context file for the schema you are working with:
   - GitOps → [`context/argocd.md`](context/argocd.md)
   - IAC → [`context/terragrunt.md`](context/terragrunt.md)
   - Observability → [`context/slo-budget.md`](context/slo-budget.md)
   - Incident → [`context/rollback-patterns.md`](context/rollback-patterns.md)
3. Copy the templates from `schemas/<schema>/templates/`
4. Fill `proposal.md` first and get it reviewed before continuing

If you want to contribute to the framework itself, read [`CONTRIBUTING.md`](CONTRIBUTING.md).
