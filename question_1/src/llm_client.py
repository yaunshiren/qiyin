"""后续统一封装 DeepSeek 调用的命令行占位模块。"""

import argparse
import sys
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    return argparse.ArgumentParser(
        description="统一封装后续 DeepSeek 请求、错误和重试（本阶段不调用 API）。"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """解析命令行参数，并报告大模型客户端待实现。"""
    build_parser().parse_args(argv)
    print("错误：DeepSeek 客户端待实现，本阶段不会发起外部 API 请求。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
