"""Runbook validator — validates that runbooks have all required sections."""

from pathlib import Path

REQUIRED_SECTIONS_GITOPS_IAC = ["PRE-APPLY", "APPLY", "VERIFY", "ROLLBACK"]
REQUIRED_SECTIONS_INCIDENT = ["RESPOSTA IMEDIATA", "VERIFY", "ROLLBACK"]


def validate_runbook(path: Path, schema: str) -> list[str]:
    """Validate a runbook.md file for required sections.

    Args:
        path: Path to the runbook.md file.
        schema: Schema type — gitops | iac | observability | incident

    Returns:
        List of validation errors. Empty list means valid.
    """
    # not implemented yet
    raise NotImplementedError("runbook validator — not implemented yet")


def check_required_sections(content: str, sections: list[str]) -> list[str]:
    """Check that all required section headers are present in the runbook.

    Args:
        content: Full text content of the runbook.
        sections: List of required section names (e.g. ["PRE-APPLY", "ROLLBACK"]).

    Returns:
        List of missing section names.
    """
    # not implemented yet
    raise NotImplementedError("check_required_sections — not implemented yet")


def check_rollback_has_commands(content: str) -> bool:
    """Check that the ROLLBACK section contains at least one code block.

    A ROLLBACK section without executable commands is invalid —
    it cannot be used during an incident.
    """
    # not implemented yet
    raise NotImplementedError("check_rollback_has_commands — not implemented yet")


def check_frontmatter_complete(content: str, required_fields: list[str]) -> list[str]:
    """Validate that all required frontmatter YAML fields are present and non-empty.

    Returns:
        List of missing or empty field names.
    """
    # not implemented yet
    raise NotImplementedError("check_frontmatter_complete — not implemented yet")
