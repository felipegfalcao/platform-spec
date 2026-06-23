---
schema: gitops
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# GitOps Proposal: [change title]

<!-- PSPEC:REQUIRED Replace the title above with a short, precise description of the change. Example: "Migrate frontend ApplicationSet to matrix generator with cluster labels" -->

## Problem

<!-- PSPEC:REQUIRED Describe the current problem this change solves. Be specific: which ApplicationSet has the issue, what behavior is incorrect, what limitation is being hit. Do not use vague language like "improve the configuration". -->

**Example**: The `frontend-apps` ApplicationSet uses the `list` generator with hardcoded clusters. Adding a new cluster requires manually updating the ApplicationSet, which caused incident INC-2024-089 when the `prod-eu-west-1` cluster was missed during the 2.4.0 version rollout.

## Motivation

<!-- PSPEC:REQUIRED Explain why solving this problem now matters. Include: current operational impact, frequency of the issue, cost of not solving it. -->

**Example**: The team adds an average of 1 cluster per quarter. Each addition carries the risk of forgetting to update ApplicationSets. Incident INC-2024-089 caused 45 minutes of service degradation in production.

## Proposed solution

<!-- PSPEC:REQUIRED Describe the solution at the design level — what will be changed in ArgoCD, not exactly how. The technical design comes in design.md. -->

**Example**: Migrate the `frontend-apps` ApplicationSet generator from `list` to `cluster` with label filters `platform/frontend: "true"`. New clusters will be included automatically once they receive the correct label, eliminating manual ApplicationSet updates.

## Alternatives considered

<!-- PSPEC:OPTIONAL List alternatives that were evaluated and why they were discarded. Minimum one alternative. -->

| Alternative | Reason discarded |
|-------------|-----------------|
| Keep `list` generator and add CI check | Does not solve the root cause; adds CI complexity |
| Use `git` generator with a clusters file | Requires maintaining a separate inventory file — two places to update |

## Expected impact

<!-- PSPEC:REQUIRED Describe the expected outcome after the change. Be measurable. -->

- Eliminate the need for manual ApplicationSet updates when adding clusters
- Reduce cluster onboarding time from ~2h (manual + review) to ~10min (label only)
- Eliminate the class of incidents caused by forgetting a cluster in an ApplicationSet

## Required approvals

<!-- PSPEC:REQUIRED List who needs to approve this proposal before proceeding to impact-analysis. -->

| Role | Name | Status |
|------|------|--------|
| SRE Lead | | Pending |
| Platform Engineer owner | | Pending |

## Dependencies

<!-- PSPEC:OPTIONAL List external changes this proposal depends on. -->

- [ ] Clusters must have the label `platform/frontend: "true"` configured before the apply

## Related links

<!-- PSPEC:OPTIONAL -->

- Related incident:
- Related ADR:
- Previous runbook:
