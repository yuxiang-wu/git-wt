# AGENTS.md - git-wt

Guidelines for AI agents working in this repository.

## Project Overview

`git-wt` is a lightweight Python CLI tool for managing git worktrees with automatic file syncing and post-create hooks. It provides an interactive TUI using Rich and Questionary.

## Build/Lint/Test Commands

```bash
# Package manager: uv (preferred) or pip
uv sync                        # Install dependencies
uv run python -m git_wt.cli    # Run locally without install
uv pip install -e .            # Install in editable mode

# Linting
uv run ruff check .            # Check for lint errors
uv run ruff check --fix .      # Auto-fix lint errors
uv run ruff format .           # Format code

# Testing
uv run pytest                  # Run all tests
uv run pytest tests/test_foo.py           # Run single test file
uv run pytest tests/test_foo.py::test_bar # Run single test function
uv run pytest -v               # Verbose output
uv run pytest -x               # Stop on first failure

# Build
uv build                       # Build wheel and sdist
```

## Project Structure

```
src/git_wt/
├── __init__.py     # Package version
├── cli.py          # Main entry point, TUI menus, user interaction
├── config.py       # Config dataclass, TOML load/save
├── git.py          # Git command wrappers (subprocess)
├── hooks.py        # Post-create hook runner
└── worktree.py     # Worktree creation, file sync logic
```

## Code Style Guidelines

### Imports

Order: standard library → third-party → local (relative: `from . import git`)

### Type Hints

**Required on all functions.** Use modern Python 3.11+ syntax:

```python
# Good
def get_branches(cwd: Path | None = None) -> list[str]:

# Bad - don't use typing module for builtins
from typing import List, Optional
def get_branches(cwd: Optional[Path] = None) -> List[str]:
```

### Data Models

Use `@dataclass` for structured data with `field(default_factory=list)` for mutable defaults.

### Path Handling

Always use `pathlib.Path`, never string paths or `os.path.join`.

### Subprocess Calls

Use `subprocess.run` with `capture_output=True, text=True, check=False`:

```python
def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, check=False)
```

### Error Handling

- Define custom exceptions in relevant module (e.g., `GitError` in `git.py`)
- Raise with descriptive messages
- Catch at CLI boundary for user-friendly output

```python
# In git.py
if result.returncode != 0:
    raise GitError(f"Failed to create worktree: {result.stderr}")

# In cli.py
try:
    create_worktree(...)
except git.GitError as e:
    console.print(f"[red]✗ {e}[/red]")
```

### Console Output (Rich)

```python
console.print("[green]✓ Success[/green]")
console.print("[yellow]⚠ Warning[/yellow]")
console.print("[red]✗ Error[/red]")
console.print("[dim]Secondary info[/dim]")
```

### Interactive Prompts (Questionary)

**Always handle `None` returns** (user pressed Ctrl+C):

```python
result = questionary.text("Input:").ask()
if result is None:
    return  # User cancelled
```

### Function Design

- Prefer module-level functions over classes
- Return tuples for multiple values: `-> tuple[list[str], list[str]]`

### Naming Conventions

- Files: `snake_case.py`
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

## Dependencies

- **rich**: Console output, tables, styling
- **questionary**: Interactive prompts, autocomplete
- **pytest**: Testing (dev)
- **ruff**: Linting and formatting (dev)

## Testing Guidelines

Tests go in `tests/` directory mirroring `src/git_wt/`. Use pytest fixtures:

```python
@pytest.fixture
def temp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo)
    return repo
```

## Git Workflow

- Main branch: `main`
- Do not commit `.envrc` or `.git-wt.toml` (project-specific config)
- Version is in `src/git_wt/__init__.py` and `pyproject.toml` (keep in sync)

## Common Tasks

### Adding a new git command wrapper

1. Add function to `git.py` following existing `_run()` pattern
2. Raise `GitError` on failure
3. Add type hints

### Adding new config options

1. Update `Config` dataclass in `config.py`
2. Update `load_config()` and `save_config()`
3. Update CLI prompts in `cli.py`

### Adding new menu actions

1. Add choice to `main_menu()` in `cli.py`
2. Create handler function
3. Call from `main()` dispatch
