"""Platform Spec CLI entry point."""

import typer
from rich import print as rprint
from rich.console import Console

from pspec import __version__
from pspec.commands import apply, init, propose, setup, validate

app = typer.Typer(
    name="pspec",
    help="Platform Spec — Spec-Driven Development for SRE and Platform Engineering.",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()

app.add_typer(setup.app, name="setup")
app.add_typer(init.app, name="init")
app.add_typer(propose.app, name="propose")
app.add_typer(validate.app, name="validate")
app.add_typer(apply.app, name="apply")


def version_callback(value: bool) -> None:
    if value:
        rprint(f"pspec version [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Platform Spec CLI — create and validate SRE change specs."""
