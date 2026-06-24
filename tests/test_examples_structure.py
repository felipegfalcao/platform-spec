"""Tests that verify example directories have the required artifacts."""

from pathlib import Path

GITOPS_REQUIRED = ["proposal.md", "impact-analysis.md", "design.md", "runbook.md", "tasks.md"]
IAC_REQUIRED = ["proposal.md", "impact-analysis.md", "design.md", "runbook.md", "tasks.md"]
INCIDENT_REQUIRED = ["postmortem.md", "rca.md"]


def test_gitops_example_has_all_artifacts(gitops_example_dir: Path) -> None:
    for artifact in GITOPS_REQUIRED:
        assert (gitops_example_dir / artifact).exists(), (
            f"Missing {artifact} in gitops-change example"
        )


def test_iac_example_has_all_artifacts(iac_example_dir: Path) -> None:
    for artifact in IAC_REQUIRED:
        assert (iac_example_dir / artifact).exists(), f"Missing {artifact} in iac-change example"


def test_gitops_example_artifacts_have_frontmatter(gitops_example_dir: Path) -> None:
    for artifact in GITOPS_REQUIRED:
        content = (gitops_example_dir / artifact).read_text(encoding="utf-8")
        assert content.startswith("---"), f"{artifact} is missing YAML frontmatter"


def test_iac_example_artifacts_have_frontmatter(iac_example_dir: Path) -> None:
    for artifact in IAC_REQUIRED:
        content = (iac_example_dir / artifact).read_text(encoding="utf-8")
        assert content.startswith("---"), f"{artifact} is missing YAML frontmatter"


def test_gitops_example_runbook_has_required_sections(gitops_example_dir: Path) -> None:
    content = (gitops_example_dir / "runbook.md").read_text(encoding="utf-8")
    for section in ["PRE-APPLY", "APPLY", "VERIFY", "ROLLBACK"]:
        assert section in content, f"runbook.md missing section: {section}"


def test_iac_example_runbook_has_required_sections(iac_example_dir: Path) -> None:
    content = (iac_example_dir / "runbook.md").read_text(encoding="utf-8")
    for section in ["PRE-APPLY", "APPLY", "VERIFY", "ROLLBACK"]:
        assert section in content, f"runbook.md missing section: {section}"
