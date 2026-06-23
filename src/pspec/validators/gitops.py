"""GitOps schema validator — validates ArgoCD ApplicationSet YAML artifacts."""

from pathlib import Path
from typing import Any


def validate_applicationset(path: Path) -> list[str]:
    """Validate a GitOps change directory.

    Checks:
    - ApplicationSet YAML is valid
    - All required frontmatter fields are present in each artifact
    - Artifact sequence is correct
    - prune: true requires explicit approval annotation

    Returns:
        List of validation errors. Empty list means valid.
    """
    # not implemented yet
    raise NotImplementedError("gitops validator — not implemented yet")


def check_prune_approval(appset_yaml: dict[str, Any]) -> bool:
    """Return True if prune: true is present without explicit approval annotation."""
    # not implemented yet
    raise NotImplementedError("check_prune_approval — not implemented yet")


def validate_generator(appset_yaml: dict[str, Any]) -> list[str]:
    """Validate ApplicationSet generator configuration.

    Checks:
    - list generator with > 5 clusters emits a warning (consider cluster generator)
    - cluster generator has required selector labels
    - matrix generator documents expected Application count
    """
    # not implemented yet
    raise NotImplementedError("validate_generator — not implemented yet")
