# AGENTS.md — platform-spec

> **Entry point for any AI agent contributing to the platform-spec project.**
> Read this document before creating, modifying, or reviewing any file in this repository.

---

## About platform-spec

**platform-spec** is a Python CLI (`pspec`) that scaffolds and validates Spec-Driven Development (SDD) artifacts for SRE and Platform Engineering teams. It is not the SDD framework itself — it is the tool that makes the framework usable.

What `pspec` does:

- `pspec init` — creates a change directory and copies the correct schema templates into it
- `pspec propose` — opens or creates the proposal artifact for a change in progress
- `pspec validate` — checks that artifacts are complete, sequenced correctly, and pass schema gates
- `pspec apply` — records a task as executed with its outcome (success / failed / skipped)

The SDD framework itself lives in `schemas/` and `scaffold/`. The CLI is the delivery mechanism for that framework.

---

## Repository structure

```text
platform-spec/
├── src/pspec/
│   ├── __init__.py             # package version (__version__)
│   ├── cli.py                  # Typer root app — registers sub-commands
│   ├── commands/               # one module per CLI command
│   │   ├── init.py             # pspec init --schema <s> --name <n>
│   │   ├── propose.py          # pspec propose [PATH]
│   │   ├── validate.py         # pspec validate [PATH] --schema --strict
│   │   └── apply.py            # pspec apply [PATH] --task --result
│   └── validators/             # schema-specific validation logic
│       ├── __init__.py
│       ├── gitops.py
│       ├── iac.py
│       └── runbook.py
├── schemas/                    # schema definitions + templates (the framework)
│   ├── gitops/
│   │   ├── schema.yaml
│   │   ├── README.md
│   │   └── templates/          # proposal, impact-analysis, design, runbook, tasks
│   ├── iac/
│   ├── observability/
│   └── incident/
├── scaffold/                   # files that pspec init installs into user repositories
│   └── AGENTS.md               # framework entry point installed in user repos
├── context/                    # domain knowledge stubs (argocd, terragrunt, slo-budget, rollback-patterns)
├── validation/                 # gate checklists per schema
├── examples/                   # fully-filled example changes used in tests
├── tests/
│   ├── conftest.py             # shared fixtures (schemas_dir, examples_dir)
│   ├── test_schemas_structure.py
│   ├── test_examples_structure.py
│   └── test_cli.py             # CLI tests via typer.testing.CliRunner
└── pyproject.toml              # entry point: pspec = "pspec.cli:app"
```

---

## Architecture

### CLI layer (`src/pspec/cli.py`)

The root `app` is a `typer.Typer`. Each command lives in its own module under `commands/` and is registered as a sub-Typer:

```python
app.add_typer(init.app, name="init")
app.add_typer(validate.app, name="validate")
```

The `--version` flag is handled by a callback on the root `@app.callback()`.

### Commands (`src/pspec/commands/`)

Each command module exposes a `typer.Typer()` named `app` and a single `@app.callback(invoke_without_command=True)` function. Commands are currently stubs — they print a "not implemented yet" message and exit. Implementing a command means replacing the stub body without changing the function signature or the option definitions.

### Validators (`src/pspec/validators/`)

Validators are pure functions that take a `Path` and return `list[str]` (errors). An empty list means valid. They are schema-specific and are called by the `validate` command.

```python
def validate_gitops_change(path: Path) -> list[str]: ...
def validate_iac_change(path: Path) -> list[str]: ...
```

### Schemas (`schemas/`)

Schemas are data, not code. A schema directory must contain:

- `schema.yaml` — `id`, `sequence`, `artifact-types`, `required-fields`, `change-types`
- `README.md` — schema-specific guidance
- `templates/*.md` — one template per artifact in the sequence, with `PSPEC:REQUIRED` / `PSPEC:OPTIONAL` markers

`pspec init` reads `schema.yaml` to know which templates to copy. `pspec validate` reads `schema.yaml` to know the required frontmatter fields and artifact sequence.

---

## Adding a new command

1. Create `src/pspec/commands/<name>.py`:

```python
"""pspec <name> — short description."""

import typer
from rich.console import Console

app = typer.Typer(help="One-line description shown in --help.")
console = Console()

@app.callback(invoke_without_command=True)
def <name>(
    path: str = typer.Argument(".", help="..."),
) -> None:
    """Docstring shown in pspec <name> --help."""
    typer.echo(f"pspec <name>: path={path} — not implemented yet")
```

1. Register in `src/pspec/cli.py`:

```python
from pspec.commands import <name>
app.add_typer(<name>.app, name="<name>")
```

1. Add tests in `tests/test_cli.py` (see Testing section below).

---

## Adding a new schema

A schema requires four things:

1. **Directory**: `schemas/<name>/`

2. **`schema.yaml`** with at minimum:

```yaml
id: <name>
sequence:
  - proposal
  - impact-analysis
  - design
  - runbook
  - tasks
artifact-types: [...]
required-fields:
  frontmatter: [schema, change-type, blast-radius, slo-impact, change-window, author, date]
change-types: [additive, modificative, destructive]
```

1. **`README.md`** explaining when to use this schema.

2. **`templates/*.md`** — one file per artifact in the sequence. Each template must start with YAML frontmatter and use `PSPEC:REQUIRED` / `PSPEC:OPTIONAL` markers.

After creating the schema directory, update:

- `tests/test_schemas_structure.py` — add the schema name to `SCHEMAS` and define its expected templates
- `src/pspec/validators/<name>.py` — validation logic
- `scaffold/AGENTS.md` — document the new schema in the Change classification section

---

## Adding a new validator

Create `src/pspec/validators/<schema>.py`. A validator module must export at least one function:

```python
def validate_<schema>_change(path: Path) -> list[str]:
    """
    Returns a list of error strings.
    An empty list means the change directory is valid.
    """
```

The `validate` command (currently a stub) will resolve the validator by schema name and call the entry function.

Validators should check:

- Required frontmatter fields are present and non-empty
- Artifact sequence is respected (impact-analysis exists before design, etc.)
- `PSPEC:REQUIRED` comment markers do not appear in the final output (they must be replaced by content)
- Schema-specific rules (e.g., `prune: true` requires approval annotation in gitops)

---

## Testing

We use pytest. Two test strategies coexist:

### Structure tests

`tests/test_schemas_structure.py` and `tests/test_examples_structure.py` verify that the repository has the expected files. They use the `schemas_dir` and `examples_dir` fixtures from `conftest.py`. No mocking.

These tests are the source of truth for "is this schema complete?" — when you add a schema, add its expected templates to the parametrize list.

### CLI tests

`tests/test_cli.py` uses `typer.testing.CliRunner` to invoke commands in-process:

```python
from typer.testing import CliRunner
from pspec.cli import app

runner = CliRunner()

def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "pspec" in result.output

def test_init_requires_schema():
    result = runner.invoke(app, ["init", "--name", "test-change"])
    assert result.exit_code != 0  # --schema is required
```

Run all tests:

```bash
uv run pytest
uv run pytest tests/test_cli.py -v        # CLI only
uv run pytest tests/test_schemas_structure.py -v  # structure only
```

---

## Development setup

```bash
git clone https://github.com/felipegfalcao/platform-spec
cd platform-spec
uv sync --extra dev
uv run pspec --help
uv run pytest
```

Linting and formatting:

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

---

## Branch naming

```text
<type>/<number>-<short-slug>   # when a GitHub issue exists
<type>/<short-slug>            # direct PR with no tracking issue
```

| Prefix | When | Example |
|---|---|---|
| `feat/` | New command or new schema | `feat/12-implement-pspec-init` |
| `fix/` | Bug in CLI or validator | `fix/34-validate-missing-frontmatter` |
| `schema/` | New or modified schema definition | `schema/add-cost-schema` |
| `docs/` | Documentation only | `docs/update-iac-readme` |
| `chore/` | CI, tooling, dependency bumps | `chore/bump-typer-0-27` |

Rules:

- Include the issue number when one exists — it makes branches traceable
- Use kebab-case, keep the slug short
- One concern per branch; `feat/` and `fix/` in the same branch is a smell

---

## AI disclosure

Every commit with AI-generated content must carry an `Assisted-by:` trailer:

```bash
feat: implement pspec validate frontmatter check

Assisted-by: Claude Sonnet 4.6 (autonomous)
```

Use `supervised` when a human reviewed the change line by line before committing. Use `autonomous` when the AI generated and the human accepted without detailed review.

Never hide AI authorship behind the operator's git identity. A commit attributed to a human account that was authored by an AI without disclosure is a false attestation.

---

## Common pitfalls

1. **Implementing a command without tests** — stubs are fine, but any non-stub implementation needs `test_cli.py` coverage before merge.

2. **Adding a schema without updating structure tests** — `test_schemas_structure.py` will not catch missing templates if the schema name is not in the `SCHEMAS` list.

3. **Changing option names in commands** — other tools and CI pipelines may call `pspec` with specific flags. Renaming `--schema` to `--type` is a breaking change; bump the minor version and update `CHANGELOG.md`.

4. **Editing templates in `schemas/` without updating `scaffold/AGENTS.md`** — if a new schema changes how the framework classifies changes, the framework guide installed in user repos must reflect that.

5. **Running pytest outside the venv** — `uv run pytest` resolves the interpreter correctly. A bare `pytest` may use a system interpreter that lacks the editable install, causing `ModuleNotFoundError` for `pspec`.
