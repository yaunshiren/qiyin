"""第一题工作流共用的路径辅助函数。"""

from pathlib import Path


def project_root() -> Path:
    """根据当前模块位置推断并返回项目根目录。"""
    return Path(__file__).resolve().parents[2]


def project_path(*parts: str) -> Path:
    """根据相对路径片段构建项目根目录下的路径。"""
    return project_root().joinpath(*parts)
