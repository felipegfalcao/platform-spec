# IAC Change Validation Checklist

Complete all items before executing any IAC task. Staging must be fully validated before prod.

---

## Pre-flight (before change window)

### Artifact completeness

- [ ] `proposal.md` — approved by SRE Lead
- [ ] `impact-analysis.md` — all REQUIRED sections complete
- [ ] `impact-analysis.md` — `destroy-and-recreate` field is accurate (confirmed via plan)
- [ ] `design.md` — HCL is valid and peer-reviewed
- [ ] `runbook.md` — PRE-APPLY, APPLY (staging first), VERIFY, ROLLBACK complete
- [ ] `tasks.md` — staging and prod tasks listed separately, in order

### Impact analysis gates

- [ ] All modified resource addresses listed (not just module names)
- [ ] `destroy-and-recreate` field reflects actual plan output (not estimated)
- [ ] Downstream dependencies mapped — teams that consume outputs notified
- [ ] State manipulation necessity assessed (`state-manipulation: true/false`)
- [ ] Rollback strategy defined for each failure scenario

### Design gates

- [ ] BEFORE state (current HCL) pasted or linked
- [ ] AFTER state (new HCL) is complete and valid
- [ ] Diff shows only intentional changes
- [ ] Expected plan output documented (resource counts: N to add, M to change, 0 to destroy)
- [ ] All ForceNew attributes verified — any attribute change that triggers ForceNew identified

### Critical: destroy-and-recreate review

- [ ] `destroy-and-recreate: false` confirmed via `terraform show -json tfplan | jq '... | select(.change.actions | contains(["delete"]))'` **OR**
- [ ] `destroy-and-recreate: true` — explicitly approved by: _______ (name + date)
      Data backup plan: _______
      Recovery time objective if recreate fails: _______

---

## Code quality gates (must pass before any environment)

- [ ] `terragrunt hclfmt --check --recursive` — exit code 0, no diff
- [ ] `terragrunt validate` — "Success! The configuration is valid."
- [ ] `checkov -d . --compact --quiet` — 0 failed checks (HIGH + CRITICAL)
      Suppressed checks documented with justification: _______
- [ ] `tflint` — 0 errors, 0 warnings (or warnings acknowledged)
- [ ] No hardcoded secrets, account IDs, or region-specific values in Component modules

---

## Staging gates (must complete before prod)

- [ ] State backup created: `terragrunt state pull > state-backup-$(date +%Y%m%d-%H%M%S).json`
- [ ] State lock confirmed free
- [ ] Plan generated and reviewed: `terragrunt plan -out=tfplan-staging`
- [ ] Plan shows expected resource counts (0 destroy if not planned)
- [ ] Zero resources with `-/+` action in plan (unless destroy+recreate was planned and approved)
- [ ] `terraform show -json tfplan | jq '.resource_changes[] | select(.change.actions | contains(["delete"])) | .address'` — output verified
- [ ] Apply in staging completed successfully
- [ ] Resource reached expected state in AWS (not just "apply complete")
- [ ] Terraform plan after apply shows "No changes" (state consistent)
- [ ] Outputs unchanged (or documented if intentionally changed)
- [ ] Services that depend on this stack are healthy in staging

---

## Error budget gate

- [ ] Error budget remaining > 20% **OR** SRE Lead approval obtained
- [ ] Not in change freeze state

---

## Production gates

- [ ] Staging fully validated (all staging gates above checked)
- [ ] New plan generated for prod (do not reuse staging tfplan)
- [ ] Prod plan reviewed and matches expected staging outcome
- [ ] State lock confirmed free for prod
- [ ] State backup created for prod
- [ ] SRE Lead aware change is starting (for blast radius high/critical)
- [ ] On-call notified in `#oncall-sre`

---

## During apply — real-time checks

- [ ] Apply output shows correct resource actions (no unexpected destroys)
- [ ] No Terraform errors during apply
- [ ] AWS resource reached expected state within timeout
- [ ] Dependent services healthy during and after modification

---

## Post-apply verification

- [ ] `terragrunt plan` after apply shows "No changes. Your infrastructure matches the configuration."
- [ ] Resource in expected state in AWS console / CLI
- [ ] Outputs unchanged (or changes documented)
- [ ] Dependent Terraform stacks healthy (run plan on dependents if outputs changed)
- [ ] Application-level health confirmed (not just infra-level)

---

## Close-out

- [ ] Change window close-out message in `#oncall-sre`
- [ ] Result documented in `tasks.md`
- [ ] State backup retained for 7 days
- [ ] If rollback occurred: postmortem opened, state backup preserved

---

## Quick reference: rollback triggers

```text
Plan shows unexpected destroy?              → STOP — do not apply — review design
Apply shows ERROR or "1 destroyed" ?        → STOP — assess before continuing to next env
Resource stuck in "modifying" > 30 min?    → Page SRE Lead — may need AWS support
Dependent service error rate spike?        → If > runbook threshold → ROLLBACK
State inconsistent after apply?            → DO NOT RE-APPLY — consult SRE Lead first
```
