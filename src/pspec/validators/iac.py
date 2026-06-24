"""IAC schema validator — validates Terraform/Terragrunt HCL artifacts."""

from pathlib import Path


def validate_iac_change(path: Path) -> list[str]:
    """Validate an IAC change directory.

    Checks:
    - All required frontmatter fields are present
    - destroy-and-recreate field is consistent with plan output (if available)
    - Artifact sequence is correct
    - Runbook contains PRE-APPLY, APPLY, VERIFY, ROLLBACK sections

    Returns:
        List of validation errors. Empty list means valid.
    """
    # not implemented yet
    raise NotImplementedError("iac validator — not implemented yet")


def validate_terragrunt_hcl(hcl_path: Path) -> list[str]:
    """Validate a terragrunt.hcl file for Composite/Component pattern compliance.

    Checks:
    - No hardcoded AWS account IDs or region names
    - No data sources in module (Component) files
    - mock_outputs_allowed_terraform_commands does not include 'apply'
    """
    # not implemented yet
    raise NotImplementedError("validate_terragrunt_hcl — not implemented yet")


def check_data_sources_in_module(module_path: Path) -> list[str]:
    """Detect data sources in Terraform module files (Component anti-pattern).

    Data sources must only appear in Composite (terragrunt.hcl) files,
    never in reusable module (Component) files.
    """
    # not implemented yet
    raise NotImplementedError("check_data_sources_in_module — not implemented yet")
