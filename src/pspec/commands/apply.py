"""pspec apply — mark a task as executed and record the result."""

import typer
from rich.console import Console

app = typer.Typer(help="Apply (execute and record) a task from a spec change.")
console = Console()


@app.callback(invoke_without_command=True)
def apply(
    path: str = typer.Argument(
        ".",
        help="Path to the change directory (default: current directory).",
    ),
    task: str = typer.Option(
        None,
        "--task",
        "-t",
        help="Task ID to mark as applied (e.g. T5). If omitted, interactive selection.",
    ),
    result: str = typer.Option(
        None,
        "--result",
        "-r",
        help="Result of the task: success | failed | skipped",
    ),
) -> None:
    """Mark a spec task as executed and record the outcome.

    Validates that runbook is approved before allowing task execution.
    Records timestamp, executor, and result in tasks.md.

    Example:
        pspec apply ./changes/migrate-frontend-appset --task T5 --result success
    """
    # not implemented yet
    typer.echo(f"pspec apply: path={path}, task={task}, result={result} — not implemented yet")
