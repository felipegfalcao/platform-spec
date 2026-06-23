# Release Process

## Versioning

Platform Spec follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (`1.0.0 → 2.0.0`): Breaking changes to the artifact sequence, schema frontmatter fields, or PSPEC:REQUIRED section structure that would require existing filled templates to be updated.
- **MINOR** (`0.1.0 → 0.2.0`): New schemas, new optional template sections, new CLI commands, new context documents.
- **PATCH** (`0.1.0 → 0.1.1`): Bug fixes in templates, wording clarifications, documentation improvements, CLI bug fixes.

## Release steps

### 1. Prepare the release

```bash
# Ensure main is clean and CI is green
git checkout main && git pull

# Bump version in pyproject.toml and src/pspec/__init__.py
# Use sed or edit manually:
# version = "0.1.0"  →  version = "0.2.0"
```

### 2. Update CHANGELOG.md

Add a new section at the top (below the `<!-- insert new changelog below this comment -->` marker):

```markdown
## [0.2.0] - YYYY-MM-DD

### Added
- Brief description of new features

### Changed
- Brief description of changes

### Fixed
- Brief description of bug fixes
```

### 3. Commit and tag

```bash
git add pyproject.toml src/pspec/__init__.py CHANGELOG.md
git commit -m "chore: release v0.2.0"
git tag v0.2.0
git push origin main --tags
```

### 4. Create GitHub Release

- Go to [Releases](https://github.com/felipegfalcao/platform-spec/releases)
- Click **Draft a new release**
- Select the tag `v0.2.0`
- Title: `v0.2.0`
- Body: paste the CHANGELOG section for this version
- Click **Publish release**

This triggers the `publish.yml` workflow which builds and publishes to PyPI automatically via trusted publishing.

### 5. Verify PyPI

```bash
uv tool install pspec
pspec --version
# Expected: pspec version 0.2.0
```

## Hotfix process

For critical bugs that need a patch release without merging unfinished features:

```bash
# Create hotfix branch from the tag
git checkout -b hotfix/0.1.1 v0.1.0
# Apply the fix
# Follow release steps above with version 0.1.1
```
