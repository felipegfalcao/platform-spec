"""pspec validate — validate spec artifacts against schema rules."""

import typer
from rich.console import Console

app = typer.Typer(help="Validate spec artifacts in a change directory.")
console = Console()


@app.callback(invoke_without_command=True)
def validate(
    path: str = typer.Argument(
        ".",
        help="Path to the change directory (default: current directory).",
    ),
    schema: str = typer.Option(
        None,
        "--schema",
        "-s",
        help="Override schema detection: gitops | iac | observability | incident",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Fail on warnings in addition to errors.",
    ),
) -> None:
    """Validate all spec artifacts in a change directory.

    Checks:
    - Frontmatter fields are complete and valid
    - Artifact sequence is correct (impact-analysis before design, etc.)
    - PSPEC:REQUIRED sections are not empty
    - Schema-specific gates are met

    Example:
        pspec validate ./changes/migrate-frontend-appset --strict
    """
    # not implemented yet
    typer.echo(f"pspec validate: path={path}, schema={schema}, strict={strict} — not implemented yet")
