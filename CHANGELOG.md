# Changelog

<!-- insert new changelog below this comment -->

## [0.1.0] - 2024-06-23

### Added

- Initial release of Platform Spec framework
- Four schemas: `gitops`, `iac`, `observability`, `incident`
- Full template sets for each schema (proposal → impact-analysis → design → runbook → tasks)
- Context knowledge base: `argocd.md`, `terragrunt.md`, `slo-budget.md`, `rollback-patterns.md`
- Validation checklists for `gitops`, `iac`, and `observability` schemas
- Fully filled examples: `gitops-change` (ApplicationSet migration) and `iac-change` (RDS gp3 migration)
- `AGENTS.md` — AI agent entry point with change classification rules and gate definitions
- `pspec` CLI stubs: `init`, `propose`, `validate`, `apply` commands (not yet implemented)
- Python package structure: `src/pspec/`, `validators/` stubs for gitops, iac, and runbook
- Open source infrastructure: PR template, issue templates, CI workflows, release process
