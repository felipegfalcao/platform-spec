"""pspec setup — initialize a new Platform Spec project."""

from pathlib import Path

import typer
import yaml
from rich.console import Console

from pspec import __version__

app = typer.Typer(help="Initialize a new Platform Spec project in the current directory.")
console = Console()

AI_CHOICES = ["claude", "copilot", "codex", "gpt", "gemini", "other"]
DOMAIN_CHOICES = ["gitops", "iac", "observability", "incident"]

# context files required per domain
DOMAIN_CONTEXT: dict[str, list[str]] = {
    "gitops": ["context/argocd.md"],
    "iac": ["context/terragrunt.md"],
    "observability": ["context/slo-budget.md"],
    "incident": ["context/rollback-patterns.md"],
}

# src/pspec/commands/setup.py → repo root (4 levels up)
# In a distributed package these would be bundled via importlib.resources
_REPO_ROOT = Path(__file__).parent.parent.parent.parent


def _prompt_ai() -> str:
    console.print("\n[bold]1. Which AI assistant will operate in this repository?[/bold]")
    for i, ai in enumerate(AI_CHOICES, 1):
        console.print(f"   {i}. {ai}")
    raw = typer.prompt("\nChoose", default="1")
    try:
        return AI_CHOICES[int(raw.strip()) - 1]
    except (ValueError, IndexError):
        return AI_CHOICES[0]


def _prompt_domains() -> list[str]:
    console.print("\n[bold]2. Which domains does this team use?[/bold]")
    for i, domain in enumerate(DOMAIN_CHOICES, 1):
        console.print(f"   {i}. {domain}")
    raw = typer.prompt("\nChoose (e.g. 1,3 or all)", default="all")
    if raw.strip().lower() == "all":
        return list(DOMAIN_CHOICES)
    selected = []
    for part in raw.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(DOMAIN_CHOICES):
                selected.append(DOMAIN_CHOICES[idx])
        except ValueError:
            pass
    return selected or list(DOMAIN_CHOICES)


def _write_config(target: Path, ai: str, domains: list[str]) -> None:
    pspec_dir = target / ".pspec"
    pspec_dir.mkdir(exist_ok=True)
    config = {"ai": ai, "domains": domains, "pspec_version": __version__}
    config_path = pspec_dir / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    console.print("[green]✓[/green] Generated: .pspec/config.yaml")


def _copy_agents_md(target: Path) -> None:
    import shutil

    src = _REPO_ROOT / "scaffold" / "AGENTS.md"
    if not src.exists():
        return
    dst = target / "AGENTS.md"
    if not dst.exists():
        shutil.copy(src, dst)
        console.print("[green]✓[/green] Generated: AGENTS.md")
    else:
        console.print("[yellow]~[/yellow] Skipped: AGENTS.md already exists")


def _copy_context_files(target: Path, domains: list[str]) -> None:
    import shutil

    (target / "context").mkdir(exist_ok=True)
    for domain in domains:
        for rel_path in DOMAIN_CONTEXT.get(domain, []):
            src = _REPO_ROOT / rel_path
            if not src.exists():
                continue
            dst = target / rel_path
            shutil.copy(src, dst)
            console.print(f"[green]✓[/green] Copied: {rel_path}")


def _print_next_steps(domains: list[str]) -> None:
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Read [bold]AGENTS.md[/bold] — mandatory entry point for any AI agent")
    for domain in domains:
        console.print(
            f"  2. To start a {domain} change: "
            f"[bold]pspec init --schema {domain} --name <change-name>[/bold]"
        )
    console.print()
    console.print("[dim]Config saved to .pspec/config.yaml[/dim]")


@app.callback(invoke_without_command=True)
def setup(
    path: str = typer.Argument(
        ".",
        help="Target directory to initialize (default: current directory).",
    ),
) -> None:
    """Initialize a new Platform Spec project.

    Sets up the AI agent integration, active schemas, and copies the required
    context files into the repository.

    Example:
        pspec setup
        pspec setup ./my-platform-repo
    """
    target = Path(path).resolve()

    console.print()
    console.print("[bold]Platform Spec — Project Setup[/bold]")
    console.print("─" * 42)

    ai = _prompt_ai()
    domains = _prompt_domains()

    console.print()
    _write_config(target, ai, domains)
    _copy_agents_md(target)
    _copy_context_files(target, domains)
    _print_next_steps(domains)
