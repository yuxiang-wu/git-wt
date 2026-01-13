from pathlib import Path
import shlex
import subprocess

from rich.console import Console


def run_hooks(
    worktree_path: Path, hooks: list[str], console: Console
) -> list[tuple[str, bool]]:
    results = []

    for hook in hooks:
        hook_path = worktree_path / hook

        if hook_path.exists():
            cmd = [str(hook_path)]
        else:
            cmd = shlex.split(hook)

        console.print(f"  [dim]Running: {hook}[/dim]")

        result = subprocess.run(
            cmd,
            cwd=worktree_path,
            capture_output=True,
            text=True,
            shell=False,
        )

        if result.returncode == 0:
            console.print(f"  [green]✓ {hook}[/green]")
            results.append((hook, True))
        else:
            console.print(f"  [red]✗ {hook} (exit {result.returncode})[/red]")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[:5]:
                    console.print(f"    [dim]{line}[/dim]")
            results.append((hook, False))

    return results
