from dataclasses import dataclass
from pathlib import Path
import subprocess


class GitError(Exception):
    pass


@dataclass
class Worktree:
    path: Path
    head: str
    branch: str | None
    is_bare: bool = False
    is_detached: bool = False
    is_locked: bool = False
    is_prunable: bool = False


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def get_repo_root(cwd: Path | None = None) -> Path:
    result = _run(["rev-parse", "--show-toplevel"], cwd=cwd)
    if result.returncode != 0:
        raise GitError("Not a git repository")
    return Path(result.stdout.strip())


def get_branches(cwd: Path | None = None) -> list[str]:
    result = _run(["branch", "--list", "--format=%(refname:short)"], cwd=cwd)
    if result.returncode != 0:
        return []
    return [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]


def get_default_branch(cwd: Path | None = None) -> str:
    result = _run(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd=cwd)
    if result.returncode == 0:
        ref = result.stdout.strip()
        return ref.replace("refs/remotes/origin/", "")

    for branch in ["main", "master"]:
        check = _run(["branch", "--list", branch], cwd=cwd)
        if check.returncode == 0 and check.stdout.strip():
            return branch

    return "main"


def get_worktrees(cwd: Path | None = None) -> list[Worktree]:
    result = _run(["worktree", "list", "--porcelain"], cwd=cwd)
    if result.returncode != 0:
        raise GitError(f"Failed to list worktrees: {result.stderr}")

    worktrees = []
    current: dict = {}

    for line in result.stdout.split("\n"):
        line = line.strip()
        if not line:
            if current and "path" in current:
                worktrees.append(
                    Worktree(
                        path=Path(current["path"]),
                        head=current.get("head", ""),
                        branch=current.get("branch"),
                        is_bare=current.get("bare", False),
                        is_detached=current.get("detached", False),
                        is_locked=current.get("locked", False),
                        is_prunable=current.get("prunable", False),
                    )
                )
            current = {}
            continue

        if line.startswith("worktree "):
            current["path"] = line[9:]
        elif line.startswith("HEAD "):
            current["head"] = line[5:]
        elif line.startswith("branch "):
            branch = line[7:]
            current["branch"] = branch.replace("refs/heads/", "")
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True
        elif line == "locked":
            current["locked"] = True
        elif line == "prunable":
            current["prunable"] = True

    if current and "path" in current:
        worktrees.append(
            Worktree(
                path=Path(current["path"]),
                head=current.get("head", ""),
                branch=current.get("branch"),
                is_bare=current.get("bare", False),
                is_detached=current.get("detached", False),
                is_locked=current.get("locked", False),
                is_prunable=current.get("prunable", False),
            )
        )

    return worktrees


def is_dirty(path: Path) -> bool:
    result = _run(["status", "--porcelain"], cwd=path)
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())


def add_worktree(
    path: Path,
    branch: str,
    new_branch: bool = False,
    base: str | None = None,
    cwd: Path | None = None,
) -> None:
    args = ["worktree", "add"]

    if new_branch:
        args.extend(["-b", branch])
        args.append(str(path))
        if base:
            args.append(base)
    else:
        args.append(str(path))
        args.append(branch)

    result = _run(args, cwd=cwd)
    if result.returncode != 0:
        raise GitError(f"Failed to create worktree: {result.stderr}")


def remove_worktree(path: Path, force: bool = False, cwd: Path | None = None) -> None:
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(path))

    result = _run(args, cwd=cwd)
    if result.returncode != 0:
        raise GitError(f"Failed to remove worktree: {result.stderr}")


def branch_exists(branch: str, cwd: Path | None = None) -> bool:
    result = _run(["rev-parse", "--verify", f"refs/heads/{branch}"], cwd=cwd)
    return result.returncode == 0
