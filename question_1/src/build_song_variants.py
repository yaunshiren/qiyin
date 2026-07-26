"""根据 accepted 歌词生成 SongVariantPlan 的命令行占位模块。"""

import argparse
import sys
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    return argparse.ArgumentParser(
        description="使用 DeepSeek 根据 accepted 歌词生成 SongVariantPlan（待实现）。"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """解析命令行参数，并报告歌曲版本方案功能待实现。"""
    build_parser().parse_args(argv)
    print("错误：SongVariantPlan 生成功能待实现。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
