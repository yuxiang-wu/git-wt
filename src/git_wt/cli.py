import subprocess
import sys
from pathlib import Path

import questionary
from rich.console import Console
from rich.table import Table

from . import git
from .config import Config, config_exists, load_config, save_config
from .hooks import run_hooks
from .worktree import create_worktree, generate_worktree_path

console = Console()


def copy_to_clipboard(text: str) -> bool:
    try:
        subprocess.run(
            ["pbcopy"],
            input=text.encode(),
            check=True,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(),
            check=True,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    try:
        subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text.encode(),
            check=True,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    return False


def open_in_finder(path: Path) -> bool:
    try:
        subprocess.run(["open", str(path)], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(["xdg-open", str(path)], check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def setup_config(repo_root: Path) -> Config | None:
    console.print("\n[yellow]No config found. Let's create one.[/yellow]\n")

    files_input = questionary.text(
        "Files to sync (comma-separated):",
        default=".env, .envrc",
    ).ask()

    if files_input is None:
        return None

    file_paths = [f.strip() for f in files_input.split(",") if f.strip()]

    mode = questionary.select(
        "Mode:",
        choices=["copy", "symlink"],
        default="copy",
    ).ask()

    if mode is None:
        return None

    hook_input = questionary.text(
        "Post-create hook (optional):",
        default="",
    ).ask()

    if hook_input is None:
        return None

    hooks = [hook_input.strip()] if hook_input.strip() else []

    save = questionary.confirm("Save config?", default=True).ask()

    if save is None:
        return None

    config = Config(
        file_mode=mode,
        file_paths=file_paths,
        post_create_hooks=hooks,
    )

    if save:
        save_config(repo_root, config)
        console.print("[green]✓ Config saved to .git-wt.toml[/green]\n")

    return config


def edit_config(repo_root: Path, config: Config) -> Config | None:
    console.print()

    files_input = questionary.text(
        "Files to sync (comma-separated):",
        default=", ".join(config.file_paths),
    ).ask()

    if files_input is None:
        return None

    file_paths = [f.strip() for f in files_input.split(",") if f.strip()]

    mode = questionary.select(
        "Mode:",
        choices=["copy", "symlink"],
        default=config.file_mode,
    ).ask()

    if mode is None:
        return None

    hook_input = questionary.text(
        "Post-create hook (optional):",
        default=config.post_create_hooks[0] if config.post_create_hooks else "",
    ).ask()

    if hook_input is None:
        return None

    hooks = [hook_input.strip()] if hook_input.strip() else []

    new_config = Config(
        file_mode=mode,
        file_paths=file_paths,
        post_create_hooks=hooks,
    )

    save_config(repo_root, new_config)
    console.print("[green]✓ Config saved[/green]\n")

    return new_config


def new_worktree(repo_root: Path, config: Config) -> None:
    branches = git.get_branches(cwd=repo_root)

    branch = questionary.autocomplete(
        "Branch:",
        choices=branches,
        validate=lambda x: len(x.strip()) > 0 or "Branch name required",
    ).ask()

    if branch is None:
        return

    branch = branch.strip()
    default_path = generate_worktree_path(repo_root, branch)

    path_input = questionary.text(
        "Path:",
        default=str(default_path),
    ).ask()

    if path_input is None:
        return

    worktree_path = Path(path_input).expanduser().resolve()

    if worktree_path.exists():
        console.print(f"[red]✗ Path already exists: {worktree_path}[/red]")
        return

    console.print()

    try:
        synced_files, skipped_files, is_new = create_worktree(
            repo_root, branch, worktree_path, config
        )
        console.print("[green]✓ Worktree created[/green]")

        if synced_files:
            mode_verb = "Linked" if config.file_mode == "symlink" else "Copied"
            console.print(f"[green]✓ {mode_verb}: {', '.join(synced_files)}[/green]")

        if skipped_files:
            console.print(f"[yellow]⚠ Not found: {', '.join(skipped_files)}[/yellow]")

        if config.post_create_hooks:
            run_hooks(worktree_path, config.post_create_hooks, console)

        if copy_to_clipboard(str(worktree_path)):
            console.print("[green]✓ Path copied to clipboard[/green]")

    except git.GitError as e:
        console.print(f"[red]✗ {e}[/red]")


def list_worktrees(repo_root: Path) -> None:
    worktrees = git.get_worktrees(cwd=repo_root)

    if not worktrees:
        console.print("[yellow]No worktrees found[/yellow]")
        return

    table = Table()
    table.add_column("Branch", style="cyan")
    table.add_column("Path")
    table.add_column("Status")

    for wt in worktrees:
        branch = wt.branch or "(detached)"
        status = ""

        if wt.is_bare:
            status = "bare"
        elif not wt.path.exists():
            status = "[red]missing[/red]"
        elif git.is_dirty(wt.path):
            status = "[yellow]dirty[/yellow]"
        else:
            status = "[green]clean[/green]"

        table.add_row(branch, str(wt.path), status)

    console.print()
    console.print(table)
    console.print()


def remove_worktree(repo_root: Path) -> None:
    worktrees = git.get_worktrees(cwd=repo_root)

    main_worktree = repo_root
    removable = [wt for wt in worktrees if wt.path != main_worktree]

    if not removable:
        console.print("[yellow]No worktrees to remove[/yellow]")
        return

    choices = [
        questionary.Choice(
            f"{wt.branch or '(detached)'} ({wt.path})",
            value=wt,
        )
        for wt in removable
    ]

    selected = questionary.select("Select worktree to remove:", choices=choices).ask()

    if selected is None:
        return

    is_dirty = git.is_dirty(selected.path)

    if is_dirty:
        console.print("\n[yellow]⚠ Worktree has uncommitted changes![/yellow]")
        confirm = questionary.confirm("Remove anyway?", default=False).ask()
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            return

    try:
        git.remove_worktree(selected.path, force=is_dirty, cwd=repo_root)
        console.print(f"[green]✓ Removed: {selected.path}[/green]")
    except git.GitError as e:
        console.print(f"[red]✗ {e}[/red]")


def main_menu(repo_root: Path, config: Config) -> str | None:
    return questionary.select(
        "What do you want to do?",
        choices=[
            questionary.Choice("New worktree", value="new"),
            questionary.Choice("List worktrees", value="list"),
            questionary.Choice("Remove worktree", value="remove"),
            questionary.Choice("Edit config", value="config"),
            questionary.Choice("Quit", value="quit"),
        ],
    ).ask()


def main() -> int:
    try:
        repo_root = git.get_repo_root()
    except git.GitError:
        console.print("[red]✗ Not a git repository[/red]")
        return 1

    if config_exists(repo_root):
        config = load_config(repo_root)
    else:
        config = setup_config(repo_root)
        if config is None:
            return 0

    action = main_menu(repo_root, config)

    if action is None or action == "quit":
        return 0
    elif action == "new":
        new_worktree(repo_root, config)
    elif action == "list":
        list_worktrees(repo_root)
    elif action == "remove":
        remove_worktree(repo_root)
    elif action == "config":
        updated = edit_config(repo_root, config)
        if updated:
            config = updated

    return 0


if __name__ == "__main__":
    sys.exit(main())
