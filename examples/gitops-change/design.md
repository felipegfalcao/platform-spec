---
schema: gitops
change-type: modificative
blast-radius: medium
slo-impact: <0.01%
change-window: scheduled
author: jane-sre
date: 2024-03-18
---

# GitOps Design: Migrate frontend-apps ApplicationSet to cluster generator

## 1. Technical overview

The `frontend-apps` ApplicationSet generator will be changed from `list` (hardcoded clusters) to `cluster` (dynamic selection by label `platform/frontend: "true"`). The sync policy, Helm configuration, and destination namespace remain unchanged.

## 2. Current state (BEFORE)

```yaml
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
            url: https://k8s-prod-us.acme.com
          - cluster: prod-eu-west-1
            url: https://k8s-prod-eu.acme.com
          - cluster: staging-us-east-1
            url: https://k8s-staging.acme.com
  template:
    metadata:
      name: 'frontend-{{cluster}}'
    spec:
      project: platform
      source:
        repoURL: https://github.com/acme/gitops-repo
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

## 3. New state (AFTER)

```yaml
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
        repoURL: https://github.com/acme/gitops-repo
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

## 4. Diff

```diff
--- a/infrastructure/argocd/appsets/frontend-apps.yaml
+++ b/infrastructure/argocd/appsets/frontend-apps.yaml
@@ -5,13 +5,8 @@ spec:
   generators:
-    - list:
-        elements:
-          - cluster: prod-us-east-1
-            url: https://k8s-prod-us.acme.com
-          - cluster: prod-eu-west-1
-            url: https://k8s-prod-eu.acme.com
-          - cluster: staging-us-east-1
-            url: https://k8s-staging.acme.com
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

## 5. Expected generated Applications

| Generated name | Target cluster | Server | Namespace |
|----------------|----------------|--------|-----------|
| `frontend-prod-us-east-1` | prod-us-east-1 | `https://k8s-prod-us.acme.com` | `frontend` |
| `frontend-prod-eu-west-1` | prod-eu-west-1 | `https://k8s-prod-eu.acme.com` | `frontend` |
| `frontend-staging-us-east-1` | staging-us-east-1 | `https://k8s-staging.acme.com` | `frontend` |

**Total expected**: 3 Applications (same as current state)

**Name change note**: Applications will be renamed from `frontend-<cluster>` to `frontend-<name>`. ArgoCD will treat this as delete + create. Verify with `argocd app diff` before applying.

## 6. File location in GitOps repository

```text
gitops-repo/
└── infrastructure/
    └── argocd/
        └── appsets/
            └── frontend-apps.yaml    ← file to modify
```

**Branch**: `feat/frontend-appset-cluster-generator`
