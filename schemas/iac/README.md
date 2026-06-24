# IAC Schema

Schema for changes to infrastructure provisioned via Terraform and Terragrunt.

## When to use this schema

Use `iac` when the change affects any of the following:

- **Terraform modules**: creation, modification, or deletion of modules
- **Terragrunt stacks**: `terragrunt.hcl`, dependencies, inputs
- **HCL hierarchy**: `root.hcl`, `env.hcl`, `region.hcl`
- **Variables**: `.tfvars`, `terraform.tfvars`, env-specific vars
- **Backend**: S3 bucket, DynamoDB lock table, state prefix
- **Providers**: versions, configurations, aliases
- **Infrastructure resources**: any AWS/GCP/Azure resource

If the change also affects ArgoCD/GitOps, read the **MIXED changes** section in [AGENTS.md](../../AGENTS.md) — IAC always first.

## Artifact sequence

```text
proposal → impact-analysis → design → runbook → tasks
```

The `impact-analysis` must map resources that will be destroyed and recreated (`destroy-and-recreate: true`) — this is critical for assessing blast radius and the need for data backups.

## Required context files

Read [`context/terragrunt.md`](../../context/terragrunt.md) before creating any artifact. It contains:

- Composite/Component pattern: what goes in each layer
- Critical rule: data sources only in Composites, never in Components
- File hierarchy and naming conventions
- Mandatory validations before any apply

## Available templates

| Template | Description |
|----------|-------------|
| [proposal.md](templates/proposal.md) | Problem, motivation, and proposed infrastructure change |
| [impact-analysis.md](templates/impact-analysis.md) | Affected resources, destroy+recreate, downstream dependencies |
| [design.md](templates/design.md) | HCL changes, expected plan output, hierarchy |
| [runbook.md](templates/runbook.md) | PRE-APPLY with security scan, APPLY, VERIFY, ROLLBACK with state |
| [tasks.md](templates/tasks.md) | Tasks with execution environment (staging first) |

## Examples

See a fully filled example at [`examples/iac-change/`](../../examples/iac-change/).

## Validation checklist

Before executing any task, validate against [`validation/iac-checklist.md`](../../validation/iac-checklist.md).
