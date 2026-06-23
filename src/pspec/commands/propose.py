"""pspec propose — create a proposal artifact from template."""

import typer
from rich.console import Console

app = typer.Typer(help="Create or open the proposal artifact for a change.")
console = Console()


@app.callback(invoke_without_command=True)
def propose(
    path: str = typer.Argument(
        ".",
        help="Path to the change directory (default: current directory).",
    ),
) -> None:
    """Create or open the proposal artifact for a spec change.

    The proposal is the first artifact in the sequence:
    proposal → impact-analysis → design → runbook → tasks

    Example:
        pspec propose ./changes/migrate-frontend-appset
    """
    # not implemented yet
    typer.echo(f"pspec propose: path={path} — not implemented yet")
