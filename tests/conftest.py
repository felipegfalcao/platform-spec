"""Shared fixtures for Platform Spec tests."""

import pytest
from pathlib import Path


@pytest.fixture
def schemas_dir() -> Path:
    """Return the path to the schemas/ directory."""
    return Path(__file__).parent.parent / "schemas"


@pytest.fixture
def examples_dir() -> Path:
    """Return the path to the examples/ directory."""
    return Path(__file__).parent.parent / "examples"


@pytest.fixture
def gitops_example_dir(examples_dir: Path) -> Path:
    return examples_dir / "gitops-change"


@pytest.fixture
def iac_example_dir(examples_dir: Path) -> Path:
    return examples_dir / "iac-change"
