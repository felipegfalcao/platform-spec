# GitOps Schema

Schema for changes to the declarative deployment plan managed by ArgoCD.

## When to use this schema

Use `gitops` when the change affects any of the following:

- **ApplicationSet**: creation, modification, or deletion
- **Application CRD**: creation, modification, or deletion
- **App-of-Apps**: bootstrap structure, parent apps, hierarchy
- **Helm values**: `values.yaml`, `values-prod.yaml`, per-environment overrides
- **Kustomize overlays**: `kustomization.yaml`, patches, components
- **syncPolicy**: change from `automated` to `manual` or vice versa
- **targetRevision**: change from branch to SHA or tag

If the change also affects Terraform/Terragrunt, read the **MIXED changes** section in [AGENTS.md](../../AGENTS.md).

## Artifact sequence

```
proposal → impact-analysis → design → runbook → tasks
```

**Never skip steps.** The impact-analysis must be approved before the design. The runbook must exist before the tasks.

## Required context files

Read [`context/argocd.md`](../../context/argocd.md) before creating any artifact. This file contains:

- App-of-Apps pattern: correct bootstrap structure
- ApplicationSet generators: git, cluster, list, matrix with examples
- Naming rules for Applications and ApplicationSets
- When to use `automated` vs `manual` syncPolicy
- How to handle `prune` safely in production

## Available templates

| Template | Description |
|----------|-------------|
| [proposal.md](templates/proposal.md) | Problem, motivation, and proposed solution |
| [impact-analysis.md](templates/impact-analysis.md) | Affected clusters, blast radius, error budget |
| [design.md](templates/design.md) | Technical specification with expected YAML diff |
| [runbook.md](templates/runbook.md) | PRE-APPLY, APPLY, VERIFY, ROLLBACK with exact commands |
| [tasks.md](templates/tasks.md) | Executable tasks with owner and success criterion |

## Examples

See a fully filled example at [`examples/gitops-change/`](../../examples/gitops-change/).

## Validation checklist

Before executing any task, validate against [`validation/gitops-checklist.md`](../../validation/gitops-checklist.md).
