"""pspec init — initialize a new Platform Spec change directory."""

import typer
from rich.console import Console

app = typer.Typer(help="Initialize a new spec change in the current directory.")
console = Console()


@app.callback(invoke_without_command=True)
def init(
    schema: str = typer.Option(
        ...,
        "--schema",
        "-s",
        help="Schema type: gitops | iac | observability | incident",
    ),
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Short name for this change (used as directory name).",
    ),
) -> None:
    """Initialize a new spec change directory with the appropriate templates.

    Example:
        pspec init --schema gitops --name migrate-frontend-appset
    """
    # not implemented yet
    typer.echo(f"pspec init: schema={schema}, name={name} — not implemented yet")
