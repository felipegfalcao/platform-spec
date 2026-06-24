# Development Notes

Platform Spec is an SDD (Spec-Driven Development) framework for SRE and Platform Engineering teams. This document orients contributors to the repository structure, development setup, and key design decisions.

## Essential project documents

| Document | Role |
|----------|------|
| [README.md](README.md) | User-facing overview of Platform Spec and the SDD workflow |
| [DEVELOPMENT.md](DEVELOPMENT.md) | This document |
| [AGENTS.md](AGENTS.md) | AI agent entry point — change classification rules and schema gates |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution process, PR expectations, and testing requirements |
| [.github/RELEASE-PROCESS.md](.github/RELEASE-PROCESS.md) | Release workflow, versioning, and changelog process |

## Repository structure

| Path | Role |
|------|------|
| `schemas/` | Schema definitions and templates. Each schema has `schema.yaml`, `README.md`, and `templates/`. |
| `context/` | Knowledge base documents read by AI agents before creating artifacts |
| `validation/` | Gate checklists used before executing any change |
| `examples/` | Fully filled template examples for each schema |
| `src/pspec/` | Python CLI source (`pspec` command) |
| `src/pspec/commands/` | One file per CLI command (`init`, `propose`, `validate`, `apply`) |
| `src/pspec/validators/` | Schema-specific validation logic |
| `tests/` | pytest tests for CLI and validators |

## Development setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install for development

```bash
# Clone the repository
git clone https://github.com/felipegfalcao/platform-spec.git
cd platform-spec

# Install with dev dependencies
uv sync --extra dev

# Verify installation
uv run pspec --version
```

### Run tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/pspec --cov-report=term-missing

# Specific test file
uv run pytest tests/test_validators_runbook.py -v
```

### Run linters

```bash
# Python linting
uvx ruff check src/

# Markdown linting
uvx markdownlint-cli2 '**/*.md'

# Format Python (auto-fix)
uvx ruff format src/
```

## Key design decisions

### Why impact-analysis before design?

Design without knowing the blast radius is the root cause of most platform incidents. The framework enforces the impact-analysis → design order because:

1. Design decisions (e.g., which generator to use) depend on blast radius
2. Reviewers need impact context to review design meaningfully
3. Runbook rollback procedures depend on impact-analysis data

### Why runbook before tasks?

Tasks are units of execution. Executing a task without a tested rollback procedure means working without a safety net. In SRE, any change that cannot be rolled back in under 15 minutes requires special approval — the framework enforces this by making runbook a prerequisite for tasks.

### Why AGENTS.md is the most critical file

AGENTS.md is the entry point for AI agents. A misclassification in AGENTS.md (e.g., a change that should be IAC being classified as GitOps) means the wrong schema is used, the wrong context is read, and the wrong gates are checked. Changes to AGENTS.md require the most careful review.

### Template markers: PSPEC:REQUIRED vs PSPEC:OPTIONAL

- `<!-- PSPEC:REQUIRED instruction -->`: the section must be filled with real data. An AI agent that leaves this empty or fills it with placeholder text is violating the contract.
- `<!-- PSPEC:OPTIONAL instruction -->`: the section may be skipped if not applicable, but the agent should explicitly state "N/A — [reason]" rather than silently omitting it.

## Adding a new schema

1. Create `schemas/<name>/schema.yaml` — define artifact sequence and gates
2. Create `schemas/<name>/README.md` — explain when to use the schema
3. Create `schemas/<name>/templates/` — one file per artifact in the sequence
4. Add classification rules to `AGENTS.md` under "Change classification"
5. Create `context/<name>.md` — knowledge base for the new domain
6. Create `validation/<name>-checklist.md` — gate checklist
7. Create `examples/<name>-change/` — at least one fully filled example
8. Open a PR with the `[Schema]:` issue template as motivation
