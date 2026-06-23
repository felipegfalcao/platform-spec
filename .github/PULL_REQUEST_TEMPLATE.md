## Description

<!-- What does this PR do? Why is it needed? Link to related issue if applicable. -->

Closes #

## Type of change

- [ ] Bug fix (schema, template, or CLI behavior correction)
- [ ] New feature (new schema, template, or CLI command)
- [ ] Documentation improvement
- [ ] Refactor (no behavior change)
- [ ] CI / tooling

## Schema affected (if applicable)

- [ ] `gitops`
- [ ] `iac`
- [ ] `observability`
- [ ] `incident`
- [ ] None (CLI / tooling / docs)

## Checklist

- [ ] Templates with new sections include `<!-- PSPEC:REQUIRED -->` or `<!-- PSPEC:OPTIONAL -->` markers
- [ ] Frontmatter fields match the schema's `schema.yaml` definition
- [ ] If a template changed, the corresponding example in `examples/` was updated
- [ ] If AGENTS.md classification rules changed, the PR description explains the change
- [ ] `markdownlint` passes locally (`uv run markdownlint-cli2 '**/*.md'`)
- [ ] Python changes pass `uv run ruff check src/` and `uv run pytest`

## Testing

<!-- How did you test this change? -->

- [ ] Manually filled the template with a real SRE scenario
- [ ] Ran `pspec validate` against the affected examples (if CLI is implemented)
- [ ] Ran `uv run pytest`

## AI Disclosure

<!-- Platform Spec is AI-assisted by design. We ask for transparency about AI use in contributions. -->

- [ ] I **did not** use AI assistance for this contribution
- [ ] I **did** use AI assistance (describe below)

<!-- If you used AI, briefly describe how (e.g., "Used Claude to draft template content, reviewed and edited manually"): -->
