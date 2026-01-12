PRD: git-wt (personal TUI worktree manager)

Goal
Make git worktree fast and safe for one developer by providing an interactive TUI that:
	1.	creates worktrees with sensible defaults,
	2.	symlinks selected untracked files into the new worktree, and
	3.	optionally runs project-local hooks (setup scripts) after creation.

Non-goals (v1)
	•	Full “git wrapper” CLI parity (no complex flags-first interface).
	•	Syncing files after creation.
	•	Multi-user/team policies, remote orchestration, or CI integration.
	•	Windows support unless it’s “free” (target macOS/Linux).

⸻

Primary user
	•	Single developer (you) managing multiple parallel branches locally.

Core commands (v1)
	•	git wt (launches TUI home)
	•	Actions inside TUI:
	•	New: create a new worktree interactively
	•	List: show existing worktrees, branch, path, status
	•	Remove: remove a worktree (with safety prompts)

⸻

Key workflows

1) Create worktree (happy path)

Flow (interactive):
	1.	Choose branch:
	•	pick existing branch, or type a new branch name
	2.	Confirm worktree path:
	•	default: ../<repo>-<branch> (branch sanitized)
	3.	Before creation, show summary:
	•	branch, path, base (if creating branch), and planned symlinks + hooks
	4.	Create worktree via git worktree add ...
	5.	Symlink selected untracked files into the new worktree
	6.	Run post-create hooks (optional) in the new worktree
	7.	Show result + quick actions (open folder, copy path, remove)

2) List worktrees
	•	Show table: branch, path, HEAD short SHA, dirty status, last commit msg (optional)
	•	Provide actions: open, remove, reveal symlinked files list

3) Remove worktree
	•	Select worktree → confirm
	•	Safety checks:
	•	warn if dirty/uncommitted
	•	confirm deletion of directory
	•	do not delete branch by default (can be a later feature)

⸻

Untracked file symlinking (core feature)

Source of truth (project-local)
	•	.gitignore annotated block defines which ignored/untracked paths should be symlinked into new worktrees.

Proposed marker format (simple + robust):

# git-wt:begin
.env
.envrc
# git-wt:end

	•	Everything between markers is interpreted as paths/globs relative to repo root.
	•	Supports both files and directories.
	•	Ignores comments/blank lines.

Behavior
	•	For each configured path:
	•	If source exists in main worktree: create symlink in new worktree pointing back to source
	•	If destination exists: prompt (skip / replace / view diff-ish info)
	•	Log actions in a small summary screen (success, skipped, missing)

⸻

Hooks (post-create)

Requirement
	•	After creating the worktree (and symlinks), optionally run hooks like ./setup.sh or scripts/setup.sh.

Proposed config (project-local, minimal)

Option A (in-repo file): .git-wt.toml

[hooks]
post_create = ["./setup.sh"]

Option B (also allow .gitignore block later, but file is cleaner for commands):
	•	v1 supports .git-wt.toml (preferred) and optional fallback to a default:
	•	if ./setup.sh exists, offer to run it

Hook UX
	•	TUI prompt: “Run post-create hooks?” with remembered default per repo.
	•	Show live output in a scrollable panel; mark success/failure.

⸻

UX / TUI requirements
	•	Built with Textual (preferred) or Rich-based TUI.
	•	Interactive prompts for:
	•	branch selection/creation
	•	confirm path
	•	conflict resolution for symlinks
	•	whether to run hooks
	•	Quick keyboard navigation (n/l/r, arrows, enter, esc).

⸻

Technical design constraints
	•	Must call underlying git commands (no libgit2 requirement).
	•	Works in repo root or any subdir (detect top-level via git rev-parse --show-toplevel).
	•	Default worktree dir: ../<repo>-<branch>; sanitize branch (/ → -, spaces disallowed).

⸻

Success criteria (v1)
	•	From fresh repo state, you can:
	1.	open git wt, create a worktree in <15 seconds with minimal typing
	2.	have .env/.envrc (and other configured paths) symlinked correctly every time
	3.	optionally run setup hooks and see results clearly
	4.	list and remove worktrees safely without foot-guns

⸻

Open decisions (can be decided during implementation)
	•	Preferred base branch for “create new branch” flow (default main, but detect main/master).
	•	Whether to store per-repo remembered choices (e.g., last hook choice) in .git-wt.toml or .git/config.
	•	How to handle missing source files (warn vs prompt to create empty file).

If you want, next I can write the CLI/TUI screen map + the exact .git-wt.toml schema (minimal) + the internal command plan (git invocations + symlink logic + hook runner).
