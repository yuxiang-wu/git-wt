# git-wt

A lightweight CLI tool for managing git worktrees with automatic file syncing and post-create hooks.

## Install

```bash
uv tool install git-wt
```

## Usage

```bash
cd your-repo
git-wt
```

## Features

- Create worktrees with branch autocomplete
- Auto-copy or symlink configured files (.env, .envrc, etc.)
- Run post-create hooks (setup scripts)
- List worktrees with dirty status
- Remove worktrees with safety prompts
- Path copied to clipboard on creation

## Config

Create `.git-wt.toml` in your repo root:

```toml
[files]
mode = "copy"  # or "symlink"
paths = [".env", ".envrc"]

[hooks]
post_create = ["./setup.sh"]
```

## License

MIT
