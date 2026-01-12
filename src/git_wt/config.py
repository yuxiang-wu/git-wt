from dataclasses import dataclass, field
from pathlib import Path
import tomllib


CONFIG_FILENAME = ".git-wt.toml"


@dataclass
class Config:
    file_mode: str = "copy"
    file_paths: list[str] = field(default_factory=list)
    post_create_hooks: list[str] = field(default_factory=list)


def get_config_path(repo_root: Path) -> Path:
    return repo_root / CONFIG_FILENAME


def config_exists(repo_root: Path) -> bool:
    return get_config_path(repo_root).exists()


def load_config(repo_root: Path) -> Config:
    config_path = get_config_path(repo_root)
    if not config_path.exists():
        return Config()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    files = data.get("files", {})
    hooks = data.get("hooks", {})

    return Config(
        file_mode=files.get("mode", "copy"),
        file_paths=files.get("paths", []),
        post_create_hooks=hooks.get("post_create", []),
    )


def save_config(repo_root: Path, config: Config) -> None:
    config_path = get_config_path(repo_root)

    lines = ["[files]"]
    lines.append(f'mode = "{config.file_mode}"')
    paths_str = ", ".join(f'"{p}"' for p in config.file_paths)
    lines.append(f"paths = [{paths_str}]")
    lines.append("")
    lines.append("[hooks]")
    hooks_str = ", ".join(f'"{h}"' for h in config.post_create_hooks)
    lines.append(f"post_create = [{hooks_str}]")
    lines.append("")

    config_path.write_text("\n".join(lines))
