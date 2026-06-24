"""Tests that verify schema directories have the required structure."""

from pathlib import Path

import pytest
import yaml

SCHEMAS = ["gitops", "iac", "observability", "incident"]

GITOPS_IAC_OBS_TEMPLATES = [
    "proposal.md",
    "impact-analysis.md",
    "design.md",
    "runbook.md",
    "tasks.md",
]

INCIDENT_TEMPLATES = [
    "postmortem.md",
    "rca.md",
    "runbook.md",
]


@pytest.mark.parametrize("schema", SCHEMAS)
def test_schema_has_schema_yaml(schemas_dir: Path, schema: str) -> None:
    assert (schemas_dir / schema / "schema.yaml").exists()


@pytest.mark.parametrize("schema", SCHEMAS)
def test_schema_has_readme(schemas_dir: Path, schema: str) -> None:
    assert (schemas_dir / schema / "README.md").exists()


@pytest.mark.parametrize("schema", SCHEMAS)
def test_schema_yaml_is_valid(schemas_dir: Path, schema: str) -> None:
    schema_file = schemas_dir / schema / "schema.yaml"
    content = yaml.safe_load(schema_file.read_text(encoding="utf-8"))
    assert "id" in content
    assert "sequence" in content


@pytest.mark.parametrize("template", GITOPS_IAC_OBS_TEMPLATES)
@pytest.mark.parametrize("schema", ["gitops", "iac", "observability"])
def test_standard_schema_has_all_templates(schemas_dir: Path, schema: str, template: str) -> None:
    assert (schemas_dir / schema / "templates" / template).exists(), (
        f"Schema '{schema}' is missing template '{template}'"
    )


@pytest.mark.parametrize("template", INCIDENT_TEMPLATES)
def test_incident_schema_has_all_templates(schemas_dir: Path, template: str) -> None:
    assert (schemas_dir / "incident" / "templates" / template).exists()


@pytest.mark.parametrize("schema", ["gitops", "iac", "observability"])
def test_standard_templates_have_frontmatter(schemas_dir: Path, schema: str) -> None:
    templates_dir = schemas_dir / schema / "templates"
    for template_file in templates_dir.glob("*.md"):
        content = template_file.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            f"Template {schema}/templates/{template_file.name} is missing YAML frontmatter"
        )
