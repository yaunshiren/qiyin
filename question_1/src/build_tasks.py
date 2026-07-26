"""创建 LyricsTask 和正式 SongTask 的命令行占位模块。"""

import argparse
import sys
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    return argparse.ArgumentParser(
        description="由 Python 创建 LyricsTask，并仅为 accepted 歌词创建 SongTask（待实现）。"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """解析命令行参数，并报告任务构建功能待实现。"""
    build_parser().parse_args(argv)
    print("错误：LyricsTask 和 SongTask 构建功能待实现。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
