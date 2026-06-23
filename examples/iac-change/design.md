---
schema: iac
change-type: modificative
blast-radius: medium
slo-impact: 0.01-0.1%
change-window: required
destroy-and-recreate: false
state-manipulation: false
affects-other-teams: true
author: bob-sre
date: 2024-03-20
---

# IAC Design: Migrate api-db RDS storage from gp2 to gp3

## 1. Technical overview

Add three optional input variables to the `rds-postgres` Component (`storage_type`, `iops`, `storage_throughput`), then configure the `api-db` Composite stacks with gp3 values. The Component change is backward-compatible — existing stacks that do not set these inputs continue using the `gp2` default.

## 2. Component changes — `modules/rds-postgres/variables.tf`

```hcl
# Add to end of file — backward-compatible (all new variables have defaults)
variable "storage_type" {
  type        = string
  description = "RDS storage type. Valid values: gp2, gp3, io1."
  default     = "gp2"
  validation {
    condition     = contains(["gp2", "gp3", "io1"], var.storage_type)
    error_message = "storage_type must be one of: gp2, gp3, io1."
  }
}

variable "iops" {
  type        = number
  description = "Provisioned IOPS. Required when storage_type is gp3 (min 3000) or io1."
  default     = null
}

variable "storage_throughput" {
  type        = number
  description = "Storage throughput in MiB/s. Only valid for gp3."
  default     = null
}
```

## 3. Component changes — `modules/rds-postgres/main.tf`

```diff
 resource "aws_db_instance" "this" {
   identifier        = var.identifier
   engine            = var.engine
   instance_class    = var.instance_class
   allocated_storage = var.allocated_storage
-  storage_type      = "gp2"
+  storage_type      = var.storage_type
+  iops              = var.iops
+  storage_throughput = var.storage_throughput
   username          = var.username
   password          = var.password
 }
```

## 4. Composite changes — `stacks/prod/databases/api-db/terragrunt.hcl`

```diff
 inputs = {
   identifier        = "api-production"
   engine            = "postgres"
   instance_class    = "db.t3.medium"
   allocated_storage = 100
+  storage_type      = "gp3"
+  iops              = 6000
+  storage_throughput = 250
 }
```

## 5. Composite changes — `stacks/staging/databases/api-db/terragrunt.hcl`

```diff
 inputs = {
   identifier        = "api-staging"
   engine            = "postgres"
   instance_class    = "db.t3.micro"
   allocated_storage = 20
+  storage_type      = "gp3"
+  iops              = 3000
+  storage_throughput = 125
 }
```

## 6. Expected terraform plan output

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

**STOP condition**: If plan shows `1 to destroy` or any `-/+` marker, do not apply.

## 7. Outputs unchanged

| Output | Before | After |
|--------|--------|-------|
| `endpoint` | `api-staging.xxx.rds.amazonaws.com` | **unchanged** |
| `identifier` | `api-staging` | **unchanged** |
| `port` | `5432` | **unchanged** |

## 8. Cost change

| Resource | Before | After | Delta |
|----------|--------|-------|-------|
| api-db prod | $138/mo (gp2) | $95/mo (gp3 6k IOPS) | -$43/mo |
| api-db replica | $138/mo | $95/mo | -$43/mo |
| **Total** | **$276/mo** | **$190/mo** | **-$86/mo** |
