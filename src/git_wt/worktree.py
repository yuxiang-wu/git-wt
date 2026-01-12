from pathlib import Path
import re
import shutil

from . import git
from .config import Config


def sanitize_branch_name(branch: str) -> str:
    sanitized = branch.replace("/", "-").replace(" ", "-")
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", sanitized)
    return sanitized


def generate_worktree_path(repo_root: Path, branch: str) -> Path:
    repo_name = repo_root.name
    sanitized = sanitize_branch_name(branch)
    return repo_root.parent / f"{repo_name}-{sanitized}"


def copy_files(source_root: Path, target_root: Path, paths: list[str]) -> list[str]:
    copied = []
    for path_str in paths:
        source = source_root / path_str
        target = target_root / path_str

        if not source.exists():
            continue

        target.parent.mkdir(parents=True, exist_ok=True)

        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)

        copied.append(path_str)

    return copied


def symlink_files(source_root: Path, target_root: Path, paths: list[str]) -> list[str]:
    linked = []
    for path_str in paths:
        source = source_root / path_str
        target = target_root / path_str

        if not source.exists():
            continue

        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() or target.is_symlink():
            if target.is_symlink():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

        target.symlink_to(source.resolve())
        linked.append(path_str)

    return linked


def create_worktree(
    repo_root: Path,
    branch: str,
    worktree_path: Path,
    config: Config,
) -> tuple[list[str], bool]:
    is_new_branch = not git.branch_exists(branch, cwd=repo_root)

    if is_new_branch:
        base = git.get_default_branch(cwd=repo_root)
        git.add_worktree(
            worktree_path, branch, new_branch=True, base=base, cwd=repo_root
        )
    else:
        git.add_worktree(worktree_path, branch, cwd=repo_root)

    if config.file_mode == "symlink":
        synced_files = symlink_files(repo_root, worktree_path, config.file_paths)
    else:
        synced_files = copy_files(repo_root, worktree_path, config.file_paths)

    return synced_files, is_new_branch
