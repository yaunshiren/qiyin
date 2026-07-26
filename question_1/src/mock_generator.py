"""只模拟 SongTask 音乐结果的命令行占位模块。"""

import argparse
import sys
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    return argparse.ArgumentParser(
        description="生成不含音频的 MockMusicResult，且 is_simulated=true（待实现）。"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """解析命令行参数，并报告音乐结果模拟功能待实现。"""
    build_parser().parse_args(argv)
    print("错误：MockMusicResult 模拟功能待实现，不会创建 WAV 或 MP3。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
