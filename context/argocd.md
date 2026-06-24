# Context: ArgoCD — Padrões e Convenções

> Leia este arquivo antes de criar qualquer artefato do schema `gitops`.

---

## 1. Padrão App-of-Apps

### Estrutura correta

```text
argocd/
├── bootstrap/
│   └── root-app.yaml          ← Application que o ArgoCD gerencia a si mesmo
├── platform/
│   └── platform-appset.yaml   ← ApplicationSet que cria Applications de infra
└── apps/
    ├── frontend-appset.yaml
    └── backend-appset.yaml
```

### Hierarquia de bootstrap

```text
Cluster (manual bootstrap)
└── root-app (Application CRD aplicado manualmente 1x)
    └── platform-appset (ApplicationSet)
        ├── monitoring-app
        ├── ingress-app
        └── cert-manager-app
    └── frontend-appset (ApplicationSet)
        ├── frontend-prod-us
        └── frontend-prod-eu
```

**Regra crítica**: `root-app.yaml` é o **único** recurso aplicado manualmente no cluster. Todo o resto é gerenciado pelo ArgoCD via App-of-Apps.

**Anti-pattern**: Aplicar Application CRDs diretamente com `kubectl apply`. Se você está fazendo isso fora do bootstrap inicial, está quebrando o padrão.

---

## 2. ApplicationSet — generators disponíveis

### 2.1 Generator `list` — clusters hardcoded

```yaml
generators:
  - list:
      elements:
        - cluster: prod-us-east-1
          url: https://k8s-prod-us.example.com
          values:
            region: us-east-1
            environment: production
```

**Quando usar**: Poucos clusters estáticos ou quando cada cluster tem configuração radicalmente diferente.
**Anti-pattern**: Usar `list` com mais de 5 clusters — vira manual e frágil.

### 2.2 Generator `cluster` — seleção dinâmica por label

```yaml
generators:
  - clusters:
      selector:
        matchLabels:
          platform/frontend: "true"
          environment: production
      # Variáveis disponíveis no template: {{name}}, {{server}}, {{nameNormalized}}
      # Também: qualquer metadata.labels ou metadata.annotations do cluster Secret
```

**Quando usar**: Múltiplos clusters homogêneos onde a seleção é por label.
**Prerequisito**: Cluster Secret no namespace `argocd` com os labels corretos.

```yaml
# Cluster Secret obrigatório
apiVersion: v1
kind: Secret
metadata:
  name: cluster-prod-us-east-1
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: cluster
    platform/frontend: "true"
    environment: production
    region: us-east-1
```

### 2.3 Generator `git` — directories ou files no repositório

```yaml
# Por diretório:
generators:
  - git:
      repoURL: https://github.com/org/gitops-repo
      revision: HEAD
      directories:
        - path: apps/*/overlays/production

# Por arquivo (útil para configuração por serviço):
generators:
  - git:
      repoURL: https://github.com/org/gitops-repo
      revision: HEAD
      files:
        - path: apps/**/config.json
```

**Quando usar**: Quando novos serviços são adicionados via commit de arquivo/diretório, sem editar o ApplicationSet.
**Cuidado**: `revision: HEAD` em produção é perigoso — use `revision: main` ou um SHA específico.

### 2.4 Generator `matrix` — produto cartesiano

```yaml
generators:
  - matrix:
      generators:
        - clusters:
            selector:
              matchLabels:
                environment: production
        - git:
            repoURL: https://github.com/org/gitops-repo
            revision: main
            files:
              - path: services/**/config.yaml
```

**Quando usar**: Cada serviço em cada cluster (N serviços × M clusters = N×M Applications).
**Cuidado**: Explosão de Applications. 10 serviços × 5 clusters = 50 Applications. Monitore o uso de memória do ArgoCD controller.

---

## 3. Regras críticas de ApplicationSet

### Regra: nunca criar Application CRD diretamente

```yaml
# ERRADO — nunca faça isso para serviços (exceto bootstrap root-app):
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: frontend-prod-us
  namespace: argocd
# ...

# CORRETO — sempre via ApplicationSet:
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: frontend-apps
  namespace: argocd
spec:
  generators:
    - clusters: ...
  template:
    # Application gerada automaticamente
```

**Por quê**: Applications criadas diretamente não escalam, não têm lifecycle gerenciado, e frequentemente se tornam orphaned quando clusters são adicionados/removidos.

### Regra: targetRevision com SHA em produção

```yaml
# RUIM em produção — qualquer push para main aciona sync:
targetRevision: main

# MELHOR em produção — controle explícito de quando atualizar:
targetRevision: a1b2c3d4e5f6...  # SHA específico

# OU usar uma tag versionada:
targetRevision: v2.4.0
```

**Exceção**: Se você está usando ArgoCD para GitOps true (pull-based CD), `targetRevision: main` é intencional. Documente explicitamente esta decisão no design.

### Regra: `prune: true` requer aprovação explícita em produção

```yaml
syncPolicy:
  automated:
    prune: false    # DEFAULT SEGURO — nunca deleta recursos
    selfHeal: true  # corrige drift, mas não deleta

# PERIGOSO sem revisão cuidadosa:
syncPolicy:
  automated:
    prune: true     # DELETA recursos no cluster que não existem no git
```

**Quando `prune: true` é correto**: Você gerencia o lifecycle completo dos recursos pelo git e quer garantir que nenhum recurso "fantasma" persiste no cluster.

**Risco**: Se um arquivo for acidentalmente deletado do repositório, `prune: true` deletará o recurso do cluster em produção.

---

## 4. syncPolicy — quando usar cada modo

| Modo | Configuração | Quando usar |
|------|-------------|-------------|
| Manual | `automated: false` | Produção com alto blast radius, requer aprovação humana |
| Automated | `automated: true` | Staging, dev, ou prod com confiança alta no CI |
| selfHeal | `selfHeal: true` | Quando você quer que o ArgoCD reverta mudanças manuais no cluster |
| prune | `prune: true` | Somente com revisão explícita — deleta recursos não declarados |

**Anti-pattern**: Usar `selfHeal: true` com `prune: true` sem change window em produção. Combinação pode causar deleção em cascata se o repositório tiver problemas.

---

## 5. Performance em monorepo

### Problema: repository polling em monorepo grande

ArgoCD poleia o repositório a cada `timeout.reconciliation` segundos (default: 3 min). Em monorepos com 1000+ arquivos, isso pode sobrecarregar o git server.

### Solução: `ignorePaths`

```yaml
spec:
  template:
    spec:
      source:
        # Ignorar mudanças em paths não relacionados ao app
        # (reduz triggers de sync desnecessários)
        ignorePaths:
          - "docs/**"
          - "tests/**"
          - "*.md"
```

### Solução: `targetRevision` com SHA + external trigger

Em vez de polling, usar ArgoCD Image Updater ou webhooks para triggar sync somente quando necessário.

### Sharding do ArgoCD Application Controller

Para > 500 Applications, ativar sharding:

```yaml
# argocd-application-controller deployment
env:
  - name: ARGOCD_CONTROLLER_REPLICAS
    value: "3"  # número de shards
```

---

## 6. Convenções de naming

### Applications

**Padrão**: `{serviço}-{ambiente}-{região-curta}`

```text
frontend-prod-us     ✅
frontend-production-us-east-1  ❌ (muito longo)
frontend             ❌ (sem ambiente/região — ambíguo)
```

### ApplicationSets

**Padrão**: `{serviço}-apps` ou `{domínio}-apps`

```text
frontend-apps        ✅
payment-apps         ✅
all-services-appset  ❌ (muito genérico)
```

### Projects

**Padrão**: `{time}` ou `{domínio}`

```text
platform      ✅
payment       ✅
all           ❌ (sem isolamento)
```

---

## 7. Anti-patterns comuns

| Anti-pattern | Consequência | Alternativa |
|-------------|-------------|-------------|
| Application CRD direto (não via AppSet) | Não escala, orphaned em expansão de cluster | Sempre via ApplicationSet |
| `targetRevision: main` em prod sem revisão | Qualquer push vira deploy | SHA ou tag de versão |
| `prune: true` sem change window | Deleção acidental de recursos | `prune: false` como default, `true` com aprovação |
| Generator `list` com clusters hardcoded | Manual, propenso a erro humano | Generator `cluster` com labels |
| Múltiplos Application CRDs por serviço sem AppSet | Inconsistência entre clusters | AppSet com generator cluster |
| selfHeal + prune sem monitoramento | Deleção silenciosa difícil de detectar | Alertas específicos para sync errors |

---

## 8. Glossário

| Termo | Definição |
|-------|-----------|
| **App-of-Apps** | Padrão onde uma Application gerencia outras Applications/ApplicationSets |
| **ApplicationSet** | CRD que gera Applications dinamicamente baseado em generators |
| **generator** | Fonte de dados para geração de Applications (list, cluster, git, matrix) |
| **selfHeal** | ArgoCD reverte automaticamente mudanças manuais no cluster |
| **prune** | ArgoCD deleta recursos do cluster que não existem no git |
| **sync** | Processo de aplicar o estado do git no cluster |
| **drift** | Diferença entre o estado no git e o estado no cluster |
| **orphaned** | Application criada manualmente que não tem owner (ApplicationSet) |
