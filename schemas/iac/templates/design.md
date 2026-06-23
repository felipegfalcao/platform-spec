---
schema: iac
change-type: # additive | modificative | destructive
blast-radius: # low | medium | high | critical
slo-impact: # none | <0.01% | 0.01-0.1% | >0.1%
change-window: # none | scheduled | required
destroy-and-recreate: # true | false
state-manipulation: # true | false
affects-other-teams: # true | false
author: # author-name
date: # YYYY-MM-DD
---

# IAC Design: [change title]

<!-- PSPEC:REQUIRED Complete technical specification. The HCL here must be valid and ready to commit. Consult context/terragrunt.md for Composite/Component pattern conventions before writing. -->

## 1. Technical overview

<!-- PSPEC:REQUIRED -->

**Example**: Modify the `rds-postgres` module (Component) to accept new input variables `storage_type`, `iops`, and `storage_throughput`. Update the Composite `stacks/prod/databases/api-db` with the new values. The change follows the Composite/Component pattern: the Component only exposes variables, the Composite defines the concrete values per environment.

## 2. Changes to the Component (Terraform module)

<!-- PSPEC:REQUIRED Show the change in the reusable module. Remember: Components receive everything via input variables — no data sources, no hardcoded values. -->

### 2.1 File: `modules/rds-postgres/variables.tf`

```hcl
# BEFORE — existing variables (do not remove)
variable "instance_class" {
  type        = string
  description = "RDS instance class"
}

variable "allocated_storage" {
  type        = number
  description = "Storage size in GB"
}

# AFTER — add at the end of the file
variable "storage_type" {
  type        = string
  description = "RDS storage type (gp2, gp3, io1)"
  default     = "gp2"
  validation {
    condition     = contains(["gp2", "gp3", "io1"], var.storage_type)
    error_message = "storage_type must be one of: gp2, gp3, io1"
  }
}

variable "iops" {
  type        = number
  description = "Provisioned IOPS. Required when storage_type is gp3 or io1."
  default     = null
}

variable "storage_throughput" {
  type        = number
  description = "Storage throughput in MiB/s. Only valid for gp3."
  default     = null
}
```

### 2.2 File: `modules/rds-postgres/main.tf`

```hcl
# DIFF — only changed lines
resource "aws_db_instance" "this" {
  # ... existing attributes unchanged ...
  
  # BEFORE: hardcoded storage_type
  # storage_type = "gp2"
  
  # AFTER: via variable
  storage_type       = var.storage_type
  iops               = var.iops
  storage_throughput = var.storage_throughput
}
```

## 3. Changes to the Composite (Terragrunt stack)

<!-- PSPEC:REQUIRED The Composite defines the concrete values per environment. Data sources go here, never in the Component. -->

### 3.1 File: `stacks/prod/databases/api-db/terragrunt.hcl`

```hcl
# BEFORE
terraform {
  source = "../../../../modules/rds-postgres"
}

inputs = {
  instance_class    = "db.t3.medium"
  allocated_storage = 100
  db_name           = "api_production"
  # ... other inputs ...
}

# AFTER (diff)
terraform {
  source = "../../../../modules/rds-postgres"
}

inputs = {
  instance_class     = "db.t3.medium"
  allocated_storage  = 100
  db_name            = "api_production"
  # New inputs for gp3 storage:
  storage_type       = "gp3"
  iops               = 6000
  storage_throughput = 250
  # ... other inputs unchanged ...
}
```

### 3.2 File: `stacks/staging/databases/api-db/terragrunt.hcl`

```hcl
# Staging uses smaller values for cost
inputs = {
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  db_name            = "api_staging"
  storage_type       = "gp3"
  iops               = 3000       # gp3 minimum
  storage_throughput = 125        # gp3 minimum
}
```

## 4. Expected terraform plan output

<!-- PSPEC:REQUIRED Document the expected plan output. Any difference between expected and actual requires stopping and analysis. -->

### 4.1 Expected plan for staging

```
Terraform will perform the following actions:

  # aws_db_instance.this will be updated in-place
  ~ resource "aws_db_instance" "this" {
        id                  = "api-staging"
      ~ iops                = 0 -> 3000
      ~ storage_throughput  = 0 -> 125
      ~ storage_type        = "gp2" -> "gp3"
        # (all other attributes unchanged)
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

**WARNING**: If the plan shows `0 to add, 1 to change, 1 to destroy` or `-/+ resource`, STOP and review. This means the modification would cause an unplanned destroy+recreate.

### 4.2 ForceNew verification

```bash
# Before applying, confirm there are no ForceNew resources in the plan
terragrunt plan -out=tfplan
terraform show -json tfplan | jq '.resource_changes[] | select(.change.actions | contains(["delete"])) | .address'
# Expected output: no lines (zero resources deleted)
```

## 5. File locations in the repository

```
infra-repo/
├── modules/
│   └── rds-postgres/
│       ├── main.tf           ← modify aws_db_instance
│       ├── variables.tf      ← add 3 new variables
│       └── outputs.tf        ← no change
└── stacks/
    ├── prod/
    │   └── databases/
    │       └── api-db/
    │           └── terragrunt.hcl    ← add 3 new inputs
    └── staging/
        └── databases/
            └── api-db/
                └── terragrunt.hcl    ← add 3 new inputs (smaller values)
```

## 6. Inheritance hierarchy (verify compatibility)

<!-- PSPEC:REQUIRED Document how the change fits into the root.hcl > env.hcl > region.hcl > terragrunt.hcl hierarchy. -->

```
root.hcl                    ← no change (remote state, provider config)
└── stacks/prod/env.hcl     ← no change (env-level tags, account)
    └── databases/region.hcl ← no change (region, AZs)
        └── api-db/terragrunt.hcl  ← CHANGE HERE (new inputs)
```

**Root.hcl provider config** (verify the AWS provider version supports gp3):
```hcl
# Minimum required: hashicorp/aws >= 4.0 (gp3 + storage_throughput support)
# Current version in root.hcl: verify before apply
```

## 7. Affected outputs

<!-- PSPEC:REQUIRED List outputs that change and the impact on consumers. -->

| Output | BEFORE value | AFTER value | Consumers |
|--------|-------------|-------------|-----------|
| `endpoint` | `api-staging.xxx.rds.amazonaws.com` | **no change** | api-backend stack |
| `identifier` | `api-staging` | **no change** | monitoring stack |
| `port` | `5432` | **no change** | api-backend stack |

**Conclusion**: No output changes. Dependent stacks do not need to be re-applied.

## 8. Costs

<!-- PSPEC:OPTIONAL Document cost changes if relevant for approval. -->

| Resource | BEFORE cost | AFTER cost | Delta |
|----------|------------|------------|-------|
| `aws_db_instance.api_db` (prod) | $138/month (gp2, 100 GB) | $95/month (gp3, 6000 IOPS) | -$43/month |
| `aws_db_instance.api_db_replica` | $138/month | $95/month | -$43/month |
| **Total** | **$276/month** | **$190/month** | **-$86/month** |
