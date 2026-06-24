# Platform Spec

**Spec-Driven Development (SDD) framework for SRE and Platform Engineering teams.**

Platform Spec brings structured, artifact-driven change management to the infrastructure layer — where the final deliverable is not application code, but YAML, HCL, and operational procedures.

---

## Why Platform Spec?

Existing SDD frameworks (BMAD, OpenSpec, Spec Kit) are designed for feature development cycles. SRE and Platform Engineering teams work differently:

- Changes have **blast radius** — a misconfigured ApplicationSet can take down 50 services
- Every change needs a **rollback procedure** documented before execution
- **Impact analysis** must precede design, not follow it
- The artifact is a **runbook**, not a user story

Platform Spec enforces this discipline through schemas, templates, and validation gates.

---

## Schemas

| Schema | Use when |
|--------|---------|
| [`gitops`](schemas/gitops/) | Changing ArgoCD ApplicationSets, Applications, Helm values, Kustomize overlays |
| [`iac`](schemas/iac/) | Changing Terraform modules, Terragrunt stacks, AWS infrastructure |
| [`observability`](schemas/observability/) | Creating or modifying alerts, dashboards, SLOs, recording rules |
| [`incident`](schemas/incident/) | Documenting a production incident (postmortem → RCA → runbook) |

## Artifact sequence (enforced)

```text
gitops / iac / observability:
  proposal → impact-analysis → design → runbook → tasks

incident:
  postmortem → rca → runbook
```

No task can be executed without a completed and approved runbook. No design can be written without a completed impact-analysis. This is not optional.

---

## Getting started

### 1. Identify your change type

Read [AGENTS.md](AGENTS.md) — specifically the "Change classification" section. If you are using an AI agent, the agent should read AGENTS.md before doing anything else.

### 2. Read the domain context

| Schema | Required reading |
|--------|-----------------|
| gitops | [context/argocd.md](context/argocd.md) |
| iac | [context/terragrunt.md](context/terragrunt.md) |
| observability | [context/slo-budget.md](context/slo-budget.md) |
| incident | [context/rollback-patterns.md](context/rollback-patterns.md) |

### 3. Copy the templates

```text
schemas/<schema>/templates/
```

### 4. Fill artifacts in order

Start with `proposal.md`. Get approval. Then `impact-analysis.md`. Get approval. Then `design.md`. Then `runbook.md`. Only then write `tasks.md`.

### 5. Validate before executing

Run the schema checklist before any change window:

```text
validation/gitops-checklist.md
validation/iac-checklist.md
validation/observability-checklist.md
```

---

## Mixed changes (IAC + GitOps)

When a change touches both Terraform and ArgoCD, create two separate change sets. **IAC always goes first** — ArgoCD references resources that Terraform provisions.

See [AGENTS.md § Mixed changes](AGENTS.md#mixed-changes-iac--gitops) for the full protocol.

---

## Examples

- [GitOps change](examples/gitops-change/) — migrating an ApplicationSet generator
- [IAC change](examples/iac-change/) — migrating RDS storage type from gp2 to gp3

---

## Repository structure

```text
platform-spec/
├── AGENTS.md              ← AI agent entry point — read this first
├── schemas/
│   ├── gitops/            ← ArgoCD changes
│   ├── iac/               ← Terraform/Terragrunt changes
│   ├── observability/     ← Alerts, dashboards, SLOs
│   └── incident/          ← Postmortems, RCAs, operational runbooks
├── context/               ← Domain knowledge base (read before creating artifacts)
│   ├── argocd.md
│   ├── terragrunt.md
│   ├── slo-budget.md
│   └── rollback-patterns.md
├── validation/            ← Gate checklists by schema
└── examples/              ← Fully filled examples
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
