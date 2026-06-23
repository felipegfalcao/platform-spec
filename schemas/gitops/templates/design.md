---
schema: gitops
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
author: # author-name
date: # YYYY-MM-DD
---

# GitOps Design: [change title]

<!-- PSPEC:REQUIRED This document specifies the exact technical configuration to be applied. All YAML here must be ready to commit to the GitOps repository. Do not use placeholders — use real values or documented ArgoCD template variables. -->

## 1. Technical overview

<!-- PSPEC:REQUIRED Describe in 2–5 sentences what will be changed technically. -->

**Example**: The `frontend-apps` ApplicationSet will have its generator changed from `list` (hardcoded clusters) to `cluster` (dynamic selection by label `platform/frontend: "true"`). The change preserves the `syncPolicy`, `helm`, and `destination` configuration of the generated Applications. The transition is non-disruptive to ongoing syncs.

## 2. Current configuration (BEFORE state)

<!-- PSPEC:REQUIRED Show the complete current configuration of the resource to be modified. Paste the actual YAML from the cluster, not an approximation. -->

```yaml
# Current ApplicationSet — BEFORE
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: frontend-apps
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - cluster: prod-us-east-1
            url: https://k8s-prod-us.example.com
          - cluster: prod-eu-west-1
            url: https://k8s-prod-eu.example.com
          - cluster: staging-us-east-1
            url: https://k8s-staging.example.com
  template:
    metadata:
      name: 'frontend-{{cluster}}'
    spec:
      project: platform
      source:
        repoURL: https://github.com/org/gitops-repo
        targetRevision: main
        path: apps/frontend
        helm:
          valueFiles:
            - values.yaml
            - values-{{cluster}}.yaml
      destination:
        server: '{{url}}'
        namespace: frontend
      syncPolicy:
        automated:
          selfHeal: true
          prune: false
```

## 3. New configuration (AFTER state)

<!-- PSPEC:REQUIRED Show the complete configuration after the change. This YAML will be committed to the GitOps repository. -->

```yaml
# New ApplicationSet — AFTER
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: frontend-apps
  namespace: argocd
spec:
  generators:
    - clusters:
        selector:
          matchLabels:
            platform/frontend: "true"
  template:
    metadata:
      name: 'frontend-{{name}}'
    spec:
      project: platform
      source:
        repoURL: https://github.com/org/gitops-repo
        targetRevision: main
        path: apps/frontend
        helm:
          valueFiles:
            - values.yaml
            - values-{{name}}.yaml
      destination:
        server: '{{server}}'
        namespace: frontend
      syncPolicy:
        automated:
          selfHeal: true
          prune: false
```

## 4. Change diff

<!-- PSPEC:REQUIRED Show a clean diff of the changed lines. Simplifies review and serves as reference during the apply. -->

```diff
--- a/appsets/frontend-apps.yaml
+++ b/appsets/frontend-apps.yaml
@@ -5,13 +5,8 @@ spec:
   generators:
-    - list:
-        elements:
-          - cluster: prod-us-east-1
-            url: https://k8s-prod-us.example.com
-          - cluster: prod-eu-west-1
-            url: https://k8s-prod-eu.example.com
-          - cluster: staging-us-east-1
-            url: https://k8s-staging.example.com
+    - clusters:
+        selector:
+          matchLabels:
+            platform/frontend: "true"
   template:
     metadata:
-      name: 'frontend-{{cluster}}'
+      name: 'frontend-{{name}}'
     spec:
       destination:
-        server: '{{url}}'
+        server: '{{server}}'
```

## 5. Applications that will be generated

<!-- PSPEC:REQUIRED List the Applications the new ApplicationSet will generate, confirming the set is equal to or intentionally different from the current one. -->

**Expected Applications after the apply**:

| Generated name | Destination cluster | Server | Namespace |
|----------------|--------------------|----|---------|
| `frontend-prod-us-east-1` | prod-us-east-1 | `https://k8s-prod-us.example.com` | `frontend` |
| `frontend-prod-eu-west-1` | prod-eu-west-1 | `https://k8s-prod-eu.example.com` | `frontend` |
| `frontend-staging-us-east-1` | staging-us-east-1 | `https://k8s-staging.example.com` | `frontend` |

**Expected total**: 3 Applications (same as current state)

**Name differences**: Applications will be renamed from `frontend-<cluster>` to `frontend-<name>`. ArgoCD will treat this as deleting the old ones and creating new ones — verify impact with `argocd app diff` before the apply.

## 6. syncPolicy — impact analysis

<!-- PSPEC:REQUIRED Document any change to syncPolicy or confirm it remains unchanged. -->

**syncPolicy remains unchanged**:
- `automated: true` — automatic sync maintained
- `selfHeal: true` — auto-healing maintained
- `prune: false` — orphaned resources will NOT be deleted automatically (safe for this change)

**Required action**: If `prune` were `true`, the Application renaming would cause deletion of resources in the destination cluster. Confirm `prune: false` before the apply.

## 7. Required labels on clusters

<!-- PSPEC:REQUIRED for cluster generator — document the labels that must exist before the apply. -->

Each destination cluster must have the following label on the ArgoCD Secret:

```yaml
# On each cluster Secret in the argocd namespace
apiVersion: v1
kind: Secret
metadata:
  name: cluster-prod-us-east-1
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: cluster
    platform/frontend: "true"   # ← this label is required
```

**Pre-apply verification**:
```bash
kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=cluster \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.labels.platform/frontend}{"\n"}{end}'
```

Expected output: all clusters listed with value `true`.

## 8. File location in the GitOps repository

<!-- PSPEC:REQUIRED Specify the exact path in the GitOps repository where the change will be made. -->

```
gitops-repo/
└── infrastructure/
    └── argocd/
        └── appsets/
            └── frontend-apps.yaml    ← file to be modified
```

**Branch**: `feat/frontend-appset-cluster-generator`
**Commit message**: `feat(gitops): migrate frontend-apps ApplicationSet to cluster generator`

## 9. Order of operations

<!-- PSPEC:REQUIRED for changes with multiple files or resource dependencies. -->

1. Verify labels on clusters (prerequisite)
2. Commit new `frontend-apps.yaml` on the feat branch
3. Open PR for review
4. After merge into `main`, ArgoCD reconciles automatically (targetRevision: main)
5. Monitor sync of generated Applications

## 10. Residual technical risks

<!-- PSPEC:OPTIONAL Document risks not completely eliminated by the design. -->

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Application renaming causes brief OutOfSync | Medium | Monitor for 5 min post-apply; expected and non-disruptive |
| Cluster without label does not generate Application | Low | PRE-APPLY verifies all labels |
| ArgoCD controller lag in cluster discovery | Low | Wait up to 2 min for full reconciliation |
