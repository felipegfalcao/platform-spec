"""CLI tests for pspec commands via typer.testing.CliRunner."""

from pathlib import Path

from typer.testing import CliRunner

from pspec.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "pspec" in result.output


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "setup" in result.output
    assert "init" in result.output
    assert "propose" in result.output
    assert "validate" in result.output
    assert "apply" in result.output


# --- setup ---


def test_setup_defaults_creates_config(tmp_path: Path):
    result = runner.invoke(app, ["setup", str(tmp_path)], input="1\nall\n")
    assert result.exit_code == 0
    config_path = tmp_path / ".pspec" / "config.yaml"
    assert config_path.exists()


def test_setup_config_content(tmp_path: Path):
    import yaml

    runner.invoke(app, ["setup", str(tmp_path)], input="1\nall\n")
    config = yaml.safe_load((tmp_path / ".pspec" / "config.yaml").read_text())
    assert config["ai"] == "claude"
    assert set(config["domains"]) == {"gitops", "iac", "observability", "incident"}
    assert "pspec_version" in config


def test_setup_specific_ai(tmp_path: Path):
    import yaml

    runner.invoke(app, ["setup", str(tmp_path)], input="2\nall\n")  # 2 = copilot
    config = yaml.safe_load((tmp_path / ".pspec" / "config.yaml").read_text())
    assert config["ai"] == "copilot"


def test_setup_specific_domains(tmp_path: Path):
    import yaml

    runner.invoke(app, ["setup", str(tmp_path)], input="1\n1,3\n")  # gitops + observability
    config = yaml.safe_load((tmp_path / ".pspec" / "config.yaml").read_text())
    assert config["domains"] == ["gitops", "observability"]


def test_setup_invalid_domain_input_falls_back_to_all(tmp_path: Path):
    import yaml

    runner.invoke(app, ["setup", str(tmp_path)], input="1\nxyz\n")
    config = yaml.safe_load((tmp_path / ".pspec" / "config.yaml").read_text())
    assert len(config["domains"]) == 4


def test_setup_skips_agents_md_if_exists(tmp_path: Path):
    existing = tmp_path / "AGENTS.md"
    existing.write_text("# custom")
    runner.invoke(app, ["setup", str(tmp_path)], input="1\nall\n")
    assert existing.read_text() == "# custom"


# --- init ---


def test_init_requires_schema():
    result = runner.invoke(app, ["init", "--name", "test-change"])
    assert result.exit_code != 0


def test_init_requires_name():
    result = runner.invoke(app, ["init", "--schema", "gitops"])
    assert result.exit_code != 0


def test_init_stub_output():
    result = runner.invoke(app, ["init", "--schema", "gitops", "--name", "test"])
    assert result.exit_code == 0
    assert "gitops" in result.output
    assert "test" in result.output


# --- propose ---


def test_propose_stub_output():
    result = runner.invoke(app, ["propose"])
    assert result.exit_code == 0
    assert "not implemented yet" in result.output


# --- apply ---


def test_apply_stub_output():
    result = runner.invoke(app, ["apply"])
    assert result.exit_code == 0
    assert "not implemented yet" in result.output
