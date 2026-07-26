"""只评分 MockMusicResult 并生成 RankedResult 的命令行占位模块。"""

import argparse
import sys
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    return argparse.ArgumentParser(
        description="对 MockMusicResult 进行确定性评分排序并生成 RankedResult（待实现）。"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """解析命令行参数，并报告模拟结果评分功能待实现。"""
    build_parser().parse_args(argv)
    print("错误：MockMusicResult 评分和 RankedResult 生成功能待实现。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
