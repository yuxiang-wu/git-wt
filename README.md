# git-wt

A lightweight CLI tool for managing git worktrees with automatic file syncing and post-create hooks.

## Install

```bash
uv tool install git-wt
# or
pipx install git-wt
# or
pip install git-wt
```

## Usage

```bash
cd your-repo
git wt        # as a git subcommand
# or
git-wt        # standalone
```

On first run, you'll be prompted to create a config file.

## Features

- Create worktrees with branch autocomplete
- Auto-copy or symlink configured files (.env, .envrc, etc.)
- Run post-create hooks (setup scripts)
- List worktrees with dirty status
- Remove worktrees with safety prompts
- Path copied to clipboard on creation

## Config

On first run, `git-wt` will prompt you to create `.git-wt.toml` in your repo root:

```toml
[files]
mode = "copy"  # or "symlink"
paths = [".env", ".envrc"]

[hooks]
post_create = ["./setup.sh"]
```

### Options

- `files.mode`: `"copy"` (default) or `"symlink"`
- `files.paths`: List of files/directories to sync to new worktrees
- `hooks.post_create`: List of scripts to run after creating a worktree

## Why?

When working with git worktrees, you often need to:
1. Copy environment files (.env, .envrc) to each new worktree
2. Run setup scripts (install dependencies, etc.)

`git-wt` automates this workflow.

## License

MIT
