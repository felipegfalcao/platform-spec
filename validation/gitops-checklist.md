# GitOps Change Validation Checklist

Complete all items before executing any GitOps task. A task marked as executable without this checklist being complete is a protocol violation.

---

## Pre-flight (before change window)

### Artifact completeness

- [ ] `proposal.md` — approved by SRE Lead and Platform Engineer owner
- [ ] `impact-analysis.md` — all REQUIRED sections complete with real data
- [ ] `design.md` — YAML is valid and reviewed by peer
- [ ] `runbook.md` — PRE-APPLY, APPLY, VERIFY, ROLLBACK sections complete
- [ ] `tasks.md` — all tasks have owner, command, and success criterion

### Impact analysis gates

- [ ] All affected clusters explicitly listed (no "all clusters" without listing them)
- [ ] All affected ApplicationSets listed with current Application count
- [ ] Blast radius assessed with concrete failure scenario (not just "low")
- [ ] SLO impact calculated with formula, not estimated
- [ ] Change window type determined and justified
- [ ] Rollback triggers defined with objective, measurable conditions

### Design gates

- [ ] BEFORE state (current YAML) is pasted in design.md — not described, pasted
- [ ] AFTER state (new YAML) is complete and ready to commit
- [ ] Diff is clean and shows only intentional changes
- [ ] All Applications that will be generated are listed with expected count
- [ ] `syncPolicy.prune` is explicitly addressed — if `true`, requires separate approval item below

### Critical: prune review

- [ ] `prune: false` confirmed **OR**
- [ ] `prune: true` — explicitly approved by: _______ (name + date)
      Reason prune is safe here: _______

---

## ArgoCD health gates (execute immediately before change window starts)

- [ ] ArgoCD application controller pods: all `Running/Ready`
      `kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-application-controller`
- [ ] ApplicationSet controller pods: all `Running/Ready`
      `kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-applicationset-controller`
- [ ] All Applications in scope are `Synced` + `Healthy` (no pre-existing drift)
      `argocd app list -l app.kubernetes.io/managed-by=<appset-name>`
- [ ] No sync operations in progress on affected Applications
- [ ] ArgoCD version confirmed compatible with new generator/feature being used

---

## Error budget gate

- [ ] Error budget remaining > 20% **OR** SRE Lead approval obtained for < 20%
- [ ] Error budget not in freeze state (< 10%)
- [ ] SLO impact of this change calculated and within acceptable range

---

## Cluster readiness (for changes affecting cluster selectors or destinations)

- [ ] All cluster Secrets in ArgoCD namespace have required labels verified
      `kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=cluster -o wide`
- [ ] Cluster count in generator output matches expected count (dry-run verified)
- [ ] No clusters in `Unknown` or `Unreachable` status before change

---

## Communication gates

- [ ] On-call notified in `#oncall-sre` before change window
- [ ] Affected teams notified (if blast radius ≥ medium)
- [ ] Change window duration communicated

---

## During change window — real-time checks

- [ ] PRE-APPLY: all runbook pre-apply steps passed before merge
- [ ] APPLY: merge confirmed, watching ArgoCD reconciliation
- [ ] Applications generated count matches expected count
- [ ] All Applications reach `Synced` + `Healthy` within 5 minutes of merge

---

## Post-change verification

- [ ] VERIFY: all runbook verification criteria met
- [ ] Application count correct
- [ ] Health status correct for all Applications
- [ ] Smoke tests passing (if defined in runbook)
- [ ] No error spike in services managed by affected Applications
- [ ] ArgoCD controller logs clean (no reconciliation errors)

---

## Close-out

- [ ] Change window close-out message posted in `#oncall-sre`
- [ ] Result documented in `tasks.md` (success / failed-with-rollback)
- [ ] Actual duration vs. estimated recorded
- [ ] Deviations from runbook documented
- [ ] If rollback was needed: postmortem opened

---

## Quick reference: rollback decision

```bash
ApplicationSet generates wrong number of apps?    → ROLLBACK NOW (Pattern 1: git revert)
Application enters Degraded state?                → Wait 2 min → if not self-healing → ROLLBACK
Error rate spike in services?                     → If > threshold in runbook → ROLLBACK
Cannot explain what happened?                     → ROLLBACK, diagnose after
Rollback would take longer than fix forward?      → Consult SRE Lead before deciding
```
