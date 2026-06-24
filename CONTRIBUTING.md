# Contributing to Platform Spec

Thank you for your interest in contributing! Platform Spec is a community-driven SDD framework for SRE and Platform Engineering teams.

## Before you start

- Read [DEVELOPMENT.md](DEVELOPMENT.md) for repository orientation and setup
- Check [open issues](https://github.com/felipegfalcao/platform-spec/issues) to avoid duplicate work
- For significant changes (new schema, template restructure, CLI command), open an issue first to align on approach before writing code

## Types of contributions

### Templates and schemas

Schema and template contributions have the highest impact. A good template contribution:

1. Is motivated by a **real operational scenario** — not a hypothetical
2. Uses **concrete SRE examples** in comments, not placeholders like `<your-value-here>`
3. Marks sections as `<!-- PSPEC:REQUIRED -->` or `<!-- PSPEC:OPTIONAL -->` with actionable instructions
4. Comes with an updated **example** in `examples/<schema>-change/` showing the section filled

### Context documents

Context files are read by AI agents. A good context contribution:

- Includes **anti-patterns with consequences** — not just "don't do X" but "don't do X because Y happened when we did"
- Provides **working examples** (real YAML, real HCL, real PromQL)
- Has a **glossary** for domain-specific terms

### CLI (pspec)

The CLI is Python 3.11+ with Typer + Rich. To contribute:

- Each command lives in `src/pspec/commands/<command>.py`
- Validation logic lives in `src/pspec/validators/<schema>.py`
- New commands must have tests in `tests/`
- Run `uvx ruff check src/` and `uv run pytest` before opening a PR

### AGENTS.md

AGENTS.md changes require the most careful review because they affect how AI agents classify every change. When proposing a change:

- Explain the specific scenario that exposed the gap
- Show the before/after classification for a concrete example
- Consider edge cases — what else could be misclassified by the new rule?

## Development setup

```bash
git clone https://github.com/felipegfalcao/platform-spec.git
cd platform-spec
uv sync --extra dev
uv run pspec --version
uv run pytest
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for full setup instructions.

## PR process

1. Fork the repository and create a branch from `main`
2. Make your changes
3. Run linters and tests locally:

   ```bash
   uvx ruff check src/
   uvx markdownlint-cli2 '**/*.md'
   uv run pytest
   ```

4. Open a PR using the PR template — fill all sections
5. A maintainer will review within 1 week for bug fixes, 2 weeks for new features

### What makes a good PR

- Focused: one logical change per PR
- Self-contained: the PR description explains the motivation without requiring the reviewer to read linked issues
- Tested: templates are tested by filling them with a real scenario, not a synthetic one
- Consistent: naming, style, and structure match the existing schemas

## AI contributions in Platform Spec

Platform Spec is designed to be used with AI agents, so we welcome AI-assisted contributions. We require transparency:

- Disclose AI use in the PR template (there's a checkbox for this)
- AI-generated content must be reviewed and edited by the contributor — do not merge AI output without human review
- The contributor is responsible for the accuracy and safety of AI-generated template content

## Design rules (do not violate without discussion)

1. **impact-analysis before design** — the sequence is enforced by design
2. **runbook before tasks** — a task without a rollback plan is not a task
3. **PSPEC:REQUIRED sections cannot be empty** — they must contain real data, not "TBD"
4. **Examples use real SRE scenarios** — no synthetic placeholders
5. **Blast radius must be justified**, not just labeled
6. **AGENTS.md changes require two maintainer reviews**

## Commit message style

```text
type(scope): short description

type: feat | fix | docs | chore | refactor | test
scope: gitops | iac | observability | incident | cli | agents | context | validation | examples
```

Examples:

```text
feat(gitops): add matrix generator example to design template
fix(iac): correct destroy-and-recreate rollback steps
docs(agents): clarify MIXED change sequencing rule
```

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
