# AGENTS.md — Platform Spec

> **This file is the mandatory entry point for any AI agent operating in this repository.**
> Read this document in full before creating any artifact.

---

## What is Platform Spec

Platform Spec is a **Spec-Driven Development (SDD)** framework designed for SRE and Platform Engineering teams. Unlike frameworks oriented toward application code, Platform Spec manages the lifecycle of changes whose final artifact is:

- **Declarative YAML**: ArgoCD ApplicationSet, Application, App-of-Apps, Helm values, Kustomize overlays
- **Imperative-declarative HCL**: Terraform modules, Terragrunt stacks, environment variables, backends, providers
- **Observability configuration**: Prometheus alerts, Grafana dashboards, SLOs, recording rules, notification policies
- **Runbooks and operational procedures**: Postmortems, RCAs, incident runbooks

The framework enforces an artifact sequence that must be respected. No change moves to execution without an approved impact-analysis and a ready runbook.

---

## Change classification

Before creating any artifact, classify the change into one of the four schemas below. When in doubt, prefer the more restrictive schema.

### GITOPS

**Indicates**: the change affects the declarative deployment plan managed by ArgoCD.

**Triggers** (any one of these is sufficient):
- Creation, modification, or deletion of an `ApplicationSet`
- Creation, modification, or deletion of an `Application` CRD
- Changes to App-of-Apps structure (bootstrap, parent apps)
- Modification of Helm values (`values.yaml`, `values-*.yaml`)
- Modification of Kustomize overlays (`kustomization.yaml`, patches)
- Changes to `targetRevision`, `repoURL`, or `path` in any Application
- Changes to `syncPolicy` (automated → manual, enabling `selfHeal`, `prune`)
- Adding or removing clusters from an ApplicationSet generator
- Changes to `ignoreDifferences` or `ignorePaths`

**Schema**: `schemas/gitops/`
**Required context**: `context/argocd.md`

---

### IAC

**Indicates**: the change affects infrastructure provisioned via HCL code.

**Triggers** (any one of these is sufficient):
- Creation, modification, or deletion of Terraform modules
- Changes to `terragrunt.hcl` (inputs, dependencies, source)
- Changes to hierarchy files: `root.hcl`, `env.hcl`, `region.hcl`
- Changes to environment variables (`.tfvars`, `terraform.tfvars`)
- Changes to backend (S3 bucket, DynamoDB lock table, state prefix)
- Changes to providers or provider versions
- Addition, modification, or removal of infrastructure resources
- Changes to outputs consumed by other modules via dependency

**Schema**: `schemas/iac/`
**Required context**: `context/terragrunt.md`

---

### OBSERVABILITY

**Indicates**: the change affects the observability layer and SLO contracts.

**Triggers** (any one of these is sufficient):
- Creation, modification, or deletion of Prometheus alerts (AlertRule, PrometheusRule)
- Creation, modification, or deletion of Grafana dashboards
- Creation, modification, or changes to SLO definitions
- Changes to recording rules
- Changes to notification policies (alert routing, receivers)
- Changes to alert thresholds (warning, critical)
- Changes to alert evaluation windows (`for:` duration)
- Updates to scrape targets (ServiceMonitor, PodMonitor)

**Schema**: `schemas/observability/`
**Required context**: `context/slo-budget.md`

---

### INCIDENT

**Indicates**: an incident occurred and needs to be documented, or an operational runbook needs to be created or updated.

**Triggers** (any one of these is sufficient):
- Production incident resolved (requires postmortem)
- Service degradation that paged on-call
- Creation or update of an existing operational runbook
- Formal RCA requested by a stakeholder or customer
- Incident that consumed >20% of the monthly error budget

**Note**: The INCIDENT flow is inverted — learn first (postmortem → rca), then document the procedure (runbook). No code or infrastructure is changed directly under this schema.

**Schema**: `schemas/incident/`
**Required context**: `context/rollback-patterns.md`

---

## MIXED changes (IAC + GITOPS)

When a change affects both infrastructure and the deployment plan:

**Rule**: Create two separate changes. IAC always first.

**Reason**: ArgoCD references resources created by Terraform (namespaces, secrets, service accounts, IAM roles). Applying GITOPS before IAC results in an Application with status `Degraded` or `Unknown` until the resource exists.

**Mandatory sequence**:
1. Create the complete IAC change (proposal → impact-analysis → design → runbook → tasks)
2. Create the complete GITOPS change referencing the IAC change as a prerequisite
3. In the `dependencies` field of the GITOPS impact-analysis, reference the IAC change ID

**Example**: Provision a new EKS cluster via Terraform and then add it as a destination in an ApplicationSet → two separate changes, EKS first.

---

## Artifact sequence by schema

The sequence below is **inviolable**. No artifact may be created out of order.

```
GITOPS:        proposal → impact-analysis → design → runbook → tasks
IAC:           proposal → impact-analysis → design → runbook → tasks
OBSERVABILITY: proposal → impact-analysis → design → runbook → tasks
INCIDENT:      postmortem → rca → runbook
```

**Why runbook before tasks?** Tasks are execution units. Executing tasks without an approved runbook means having no documented rollback plan. In SRE, any change without a tested rollback is blocked.

---

## context/ files — what to read and when

| Schema | Required file | Content |
|--------|--------------|---------|
| GITOPS | `context/argocd.md` | ArgoCD patterns, App-of-Apps, generators, syncPolicy |
| IAC | `context/terragrunt.md` | Composite/Component pattern, HCL hierarchy, validations |
| OBSERVABILITY | `context/slo-budget.md` | Burn rate calculation, budget windows, freeze rules |
| INCIDENT | `context/rollback-patterns.md` | Rollback decision trees by technology |

**Rule**: Read the corresponding context file **before** filling out any template. Templates reference concepts defined in context/.

---

## Mandatory validation gates by schema

These gates must be completed before marking any task as executable.

### GITOPS gates
- [ ] `kubectl diff` executed and output reviewed
- [ ] ApplicationSet dry-run without template errors
- [ ] `argocd app diff` for each affected Application
- [ ] `syncPolicy` review — `prune: true` requires explicit approval in production
- [ ] Change window approved if blast radius ≥ medium
- Full checklist: `validation/gitops-checklist.md`

### IAC gates
- [ ] `terragrunt hclfmt` without diff
- [ ] `terragrunt validate` without errors
- [ ] `terragrunt plan` output reviewed and approved
- [ ] `checkov` without uncategorized critical or high failures
- [ ] `tflint` without unresolved warnings
- [ ] State lock confirmed free before apply
- Full checklist: `validation/iac-checklist.md`

### OBSERVABILITY gates
- [ ] PromQL query validated against staging environment
- [ ] Alert rule tested with `amtool check-config`
- [ ] SLO impact calculated and documented in impact-analysis
- [ ] Silence configured for post-deploy validation window
- [ ] Dashboard exported as versioned JSON in the repository
- Full checklist: `validation/observability-checklist.md`

### INCIDENT gates
- No deploy gates — INCIDENT is documentation
- Postmortem requires review by at least two SREs
- RCA requires approval from Tech Lead or Engineering Manager
- Runbook resulting from INCIDENT becomes input for the corresponding schema

---

## Required frontmatter metadata

Every artifact starts with YAML frontmatter. The fields below are mandatory:

```yaml
---
schema: gitops | iac | observability | incident
change-type: additive | modificative | destructive
blast-radius: low | medium | high | critical
slo-impact: none | <0.01% | 0.01-0.1% | >0.1%
change-window: none | scheduled | required
author: author-name
date: YYYY-MM-DD
---
```

**Definitions**:
- `additive`: only adds resources; does not remove or modify existing ones
- `modificative`: modifies existing resources; behavior changes but the resource remains
- `destructive`: removes resources, destroys state, or causes intentional downtime

---

## Anti-patterns this framework prevents

| Anti-pattern | How Platform Spec prevents it |
|-------------|-------------------------------|
| Applying Terraform without a reviewed plan | Mandatory gate: plan output in the runbook |
| ArgoCD with `prune: true` in production without review | GitOps checklist forces explicit approval |
| Improvised rollback during an incident | Runbook with ready-to-run commands is a prerequisite |
| Change without blast radius analysis | impact-analysis blocks design |
| IAC and GITOPS in the same PR | MIXED rule: two separate changes, IAC first |
| Alert without threshold validated in staging | Observability gate: query validated in staging |
| Postmortem without trackable action items | RCA template forces tasks with owner and deadline |

---

## How to use this framework

### For the AI agent

1. Read this file in full
2. Classify the change using the "Change classification" section
3. Read the corresponding context/ file
4. Create artifacts in the correct schema sequence
5. Fill all fields marked `PSPEC:REQUIRED`
6. Validate against the schema gates before marking tasks as ready

### For the engineer

1. Identify the change type
2. Copy the templates from the corresponding schema
3. Fill out the proposal and request team review
4. Complete impact-analysis with real data (not vague estimates)
5. Write the runbook with tested commands
6. Execute tasks only after the runbook is approved
7. Document the outcome in tasks (passed/failed, time, deviations)

---

## Repository structure

```
platform-spec/
├── AGENTS.md              ← you are here
├── schemas/
│   ├── gitops/            ← schema for ArgoCD changes
│   ├── iac/               ← schema for Terraform/Terragrunt changes
│   ├── observability/     ← schema for alerts, dashboards, SLOs
│   └── incident/          ← schema for postmortems and runbooks
├── context/               ← domain knowledge base (read before creating artifacts)
├── validation/            ← per-schema gate checklists
└── examples/              ← fully filled example changes
```
