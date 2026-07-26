"""第一题工作流共用的配置、路径、时间和 CSV 工具。"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


class ProjectPathError(ValueError):
    """表示路径不满足项目内相对路径约束。"""


def project_root() -> Path:
    """根据当前模块位置推断并返回项目根目录。"""
    return Path(__file__).resolve().parents[2]


def resolve_project_path(path: str | Path, *, must_exist: bool = False) -> Path:
    """解析项目内相对路径，并拒绝绝对路径和目录穿越。"""
    relative_path = Path(path)
    if relative_path.is_absolute():
        raise ProjectPathError(f"只允许项目内相对路径：{path}")

    root = project_root()
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ProjectPathError(f"路径超出项目目录：{path}") from exc

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"项目内路径不存在：{path}")
    return resolved


def project_path(*parts: str) -> Path:
    """根据相对路径片段安全构建项目根目录下的路径。"""
    return resolve_project_path(Path(*parts))


def project_relative_path(path: Path) -> str:
    """将项目内路径转换为使用正斜杠的相对路径字符串。"""
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(project_root())
    except ValueError as exc:
        raise ProjectPathError(f"路径超出项目目录：{path}") from exc
    return relative.as_posix()


def load_yaml(path: str | Path) -> dict[str, Any]:
    """读取项目内 UTF-8 YAML 文件并返回字典。"""
    yaml_path = resolve_project_path(path, must_exist=True)
    if not yaml_path.is_file():
        raise ValueError(f"YAML 路径不是文件：{path}")
    try:
        content = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML 解析失败：{path}") from exc
    if content is None:
        return {}
    if not isinstance(content, dict):
        raise ValueError(f"YAML 顶层必须是映射：{path}")
    return content


def ensure_project_directory(path: str | Path) -> Path:
    """安全创建并返回项目内目录。"""
    directory = resolve_project_path(path)
    if directory.exists() and not directory.is_dir():
        raise NotADirectoryError(f"目标路径不是目录：{path}")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def prepare_output_path(path: str | Path, *, overwrite: bool = False) -> Path:
    """准备项目内输出路径，默认拒绝覆盖已有文件。"""
    output_path = resolve_project_path(path)
    if output_path.exists():
        if output_path.is_dir():
            raise IsADirectoryError(f"输出路径是目录：{path}")
        if not overwrite:
            raise FileExistsError(f"输出文件已存在，默认禁止覆盖：{path}")
    ensure_project_directory(project_relative_path(output_path.parent))
    return output_path


def write_utf8_csv(
    path: str | Path,
    rows: Iterable[Mapping[str, object]],
    fieldnames: Sequence[str],
    *,
    overwrite: bool = False,
) -> Path:
    """将字典记录保存为项目内 UTF-8 CSV，默认禁止覆盖。"""
    output_path = prepare_output_path(path, overwrite=overwrite)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    return output_path


def write_project_bytes(
    path: str | Path,
    content: bytes,
    *,
    overwrite: bool = False,
) -> Path:
    """将二进制内容保存到项目内，默认禁止覆盖。"""
    output_path = prepare_output_path(path, overwrite=overwrite)
    output_path.write_bytes(content)
    return output_path


def utc_now_iso() -> str:
    """返回带微秒和 Z 后缀的 UTC ISO 时间。"""
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
