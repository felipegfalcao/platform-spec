# Context: Terragrunt — Padrões e Convenções

> Leia este arquivo antes de criar qualquer artefato do schema `iac`.

---

## 1. Padrão Composite/Component

O padrão Composite/Component é a base de toda organização HCL neste repositório. Entender este padrão é obrigatório antes de qualquer mudança de IAC.

### Component (módulo Terraform)

Um **Component** é um módulo Terraform reutilizável que encapsula um grupo de recursos relacionados.

**Regras de Component**:

1. **Recebe tudo via input variables** — zero valores hardcoded
2. **Zero data sources** — não faz lookups no AWS, nunca
3. **Zero referências a outros módulos** — completamente independente
4. **Outputs explícitos** — tudo que outros podem precisar deve ser output

```hcl
# modules/rds-postgres/main.tf — COMPONENT CORRETO
resource "aws_db_instance" "this" {
  identifier = var.identifier    # ← via variável
  engine     = var.engine        # ← via variável
  username   = var.username      # ← via variável
  password   = var.password      # ← via variável, nunca hardcoded
}

# ERRADO em Component:
data "aws_vpc" "main" {          # ← data source em Component é PROIBIDO
  filter { name = "tag:Name" values = ["main"] }
}
```

### Composite (stack Terragrunt)

Um **Composite** é um `terragrunt.hcl` que instancia um Component e fornece todos os inputs concretos.

**Regras de Composite**:

1. **Define inputs concretos** por ambiente
2. **Contém data sources** — aqui é o lugar correto para lookups
3. **Declara dependencies** para outros Composites
4. **Gerencia outputs** via `dependency` blocks

```hcl
# stacks/prod/databases/api-db/terragrunt.hcl — COMPOSITE CORRETO

terraform {
  source = "../../../../modules/rds-postgres"
}

# DATA SOURCES aqui são corretos — no Composite, não no Component
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["prod-vpc"]
  }
}

# Dependências de outros stacks
dependency "vpc" {
  config_path = "../../../network/vpc"
}

inputs = {
  identifier         = "api-production"
  engine             = "postgres"
  instance_class     = "db.t3.medium"
  vpc_id             = dependency.vpc.outputs.vpc_id  # ← via dependency
  username           = "api_user"
  password           = get_env("TF_VAR_DB_PASSWORD")  # ← via env var
}
```

---

## 2. Hierarquia de arquivos

```text
infra-repo/
├── root.hcl                    ← configuração global: backend, provider, tags globais
├── envs/
│   ├── prod/
│   │   ├── env.hcl             ← configuração de ambiente: account ID, env tags
│   │   └── us-east-1/
│   │       ├── region.hcl      ← configuração de região: AZs disponíveis, region-specific
│   │       ├── network/
│   │       │   └── vpc/
│   │       │       └── terragrunt.hcl   ← stack específica
│   │       └── databases/
│   │           └── api-db/
│   │               └── terragrunt.hcl   ← stack específica
│   └── staging/
│       └── ... (mesma estrutura)
└── modules/
    ├── rds-postgres/            ← Component
    ├── s3-bucket/               ← Component
    └── eks-cluster/             ← Component
```

### root.hcl — o que fica aqui

```hcl
# root.hcl
remote_state {
  backend = "s3"
  config = {
    bucket         = "terraform-state-${get_env("AWS_ACCOUNT_ID")}"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      ManagedBy   = "terraform"
      Environment = var.environment
      Repository  = "infra-repo"
    }
  }
}
EOF
}
```

### env.hcl — o que fica aqui

```hcl
# envs/prod/env.hcl
locals {
  environment = "production"
  account_id  = "123456789012"
  aws_region  = "us-east-1"
}
```

### terragrunt.hcl de stack — o que fica aqui

```hcl
# Herança da hierarquia
include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "env" {
  path   = find_in_parent_folders("env.hcl")
  expose = true  # torna locals do env.hcl acessíveis
}

# Source do módulo com versão pinada
terraform {
  source = "../../../../modules/rds-postgres//."
}

# Inputs concretos — AQUI, não no módulo
inputs = {
  environment = include.env.locals.environment
  # ...
}
```

---

## 3. Regra crítica: data sources apenas em Composites

Esta é a regra mais violada e a que causa mais problemas de manutenção.

```hcl
# PROIBIDO em módulos (Components):
# modules/rds-postgres/main.tf
data "aws_vpc" "main" {        # ← ERRO: data source no Component
  tags = { Name = "prod-vpc" }
}

resource "aws_db_subnet_group" "this" {
  subnet_ids = data.aws_vpc.main.private_subnets  # ← acoplamento oculto
}

# CORRETO: Component recebe subnet_ids como input
# modules/rds-postgres/variables.tf
variable "subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs for the RDS subnet group"
}

# E o Composite faz o lookup:
# stacks/prod/databases/api-db/terragrunt.hcl
data "aws_subnets" "private" {
  filter {
    name   = "tag:Type"
    values = ["private"]
  }
}

inputs = {
  subnet_ids = data.aws_subnets.private.ids  # ← lookup no Composite, não no Component
}
```

**Por que esta regra existe**: Components com data sources ficam acoplados a uma AWS account/região específica. Isso impossibilita reutilizar o mesmo Component em múltiplos ambientes sem modificar o módulo. Além disso, data sources no Component criam dependências implícitas difíceis de testar.

---

## 4. Mock outputs para dependências em CI

Quando um stack A depende do stack B, e você está executando CI no stack A sem ter aplicado o stack B, o Terragrunt falha ao tentar ler os outputs de B.

**Solução**: Mock outputs

```hcl
# stacks/prod/app/api-backend/terragrunt.hcl
dependency "database" {
  config_path = "../../databases/api-db"

  mock_outputs = {
    endpoint = "mock-db-endpoint.rds.amazonaws.com"
    port     = 5432
    db_name  = "api_production"
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
  # NÃO inclua "apply" nos allowed commands — mock outputs nunca em apply real
}
```

**Regra**: `mock_outputs` são permitidos apenas para `validate` e `plan` em CI. O `apply` real sempre precisa dos outputs reais.

---

## 5. Validações obrigatórias antes de qualquer apply

Execute nesta ordem. Se qualquer etapa falhar, PARE e corrija antes de prosseguir.

```bash
# 1. Formatação — deve produzir zero diff
terragrunt hclfmt --check --recursive stacks/

# 2. Validação de sintaxe e configuração
cd stacks/prod/databases/api-db
terragrunt validate

# 3. Plan — REVISAR OUTPUT ANTES DE APLICAR
terragrunt plan -out=tfplan

# 4. Verificar que plan não tem recursos sendo destruídos (se não esperado)
terraform show -json tfplan | \
  jq '.resource_changes[] | select(.change.actions | contains(["delete"])) | .address'

# 5. Security scan
checkov -d . --compact --quiet --framework terraform

# 6. Lint de módulos
cd modules/rds-postgres
tflint --init && tflint

# 7. (Opcional) Análise de custo
infracost diff --path=stacks/prod/databases/api-db
```

---

## 6. Convenções de naming de recursos

### Recursos AWS

**Padrão**: `{projeto}-{ambiente}-{componente}[-{índice}]`

```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_s3_bucket" "this" {
  bucket = "${local.name_prefix}-logs"  # → "myapp-production-logs"
}

resource "aws_db_instance" "this" {
  identifier = "${local.name_prefix}-api-db"  # → "myapp-production-api-db"
}
```

### State files

O path do state é gerado automaticamente pela configuração `key` do `root.hcl`:

```bash
{bucket}/{path_relative_to_include}/terraform.tfstate
→ my-tfstate-bucket/envs/prod/us-east-1/databases/api-db/terraform.tfstate
```

---

## 7. Anti-patterns comuns

| Anti-pattern | Consequência | Alternativa |
|-------------|-------------|-------------|
| Data sources em Components | Acoplamento a conta/região, inreutilizável | Data sources apenas em Composites |
| Valores hardcoded em módulos | Impossível reutilizar em outros ambientes | Tudo via input variables |
| Apply sem plan revisado | Destruição acidental de recursos | Plan obrigatório e revisado antes do apply |
| `mock_outputs` em apply real | Apply usa valores falsos, cria recursos incorretos | `mock_outputs_allowed_terraform_commands = ["validate", "plan"]` |
| State manipulation sem backup | State corrompido = infraestrutura não gerenciada | `state pull > backup.json` antes de qualquer manipulação |
| Dependência circular entre stacks | Deadlock no apply | Reestruturar em layers (network → compute → app) |
| Provider config no módulo (Component) | Múltiplos providers conflitantes | Provider config apenas no root.hcl |

---

## 8. Glossário

| Termo | Definição |
|-------|-----------|
| **Component** | Módulo Terraform reutilizável, recebe tudo via variables, zero data sources |
| **Composite** | Stack Terragrunt que instancia Component(s) com valores concretos por ambiente |
| **root.hcl** | Configuração global: backend S3, provider AWS, tags padrão |
| **env.hcl** | Configuração de ambiente: account ID, environment name |
| **region.hcl** | Configuração de região: região AWS, AZs disponíveis |
| **dependency** | Referência a outputs de outro stack Terragrunt |
| **mock_outputs** | Valores fictícios usados em CI quando a dependência não existe ainda |
| **state** | Arquivo que mapeia recursos Terraform para recursos reais na AWS |
| **ForceNew** | Atributo que, quando modificado, causa destroy+recreate do recurso |
