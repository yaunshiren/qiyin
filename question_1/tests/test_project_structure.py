"""验证项目初始骨架。"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUESTION_ROOT = PROJECT_ROOT / "question_1"
REQUIRED_SOURCE_FILES = {
    "__init__.py",
    "build_song_variants.py",
    "build_tasks.py",
    "build_topics.py",
    "collect_trends.py",
    "llm_client.py",
    "mock_generator.py",
    "prepare_trends.py",
    "review_lyrics.py",
    "run_tasks.py",
    "score_results.py",
    "utils.py",
}
CORE_CLI_FILES = tuple(sorted(REQUIRED_SOURCE_FILES.difference({"__init__.py", "utils.py"})))
CORE_ENTITIES = (
    "TrendRecord",
    "SongProject",
    "LyricBrief",
    "LyricsTask",
    "LyricsResult",
    "LyricsReview",
    "SongVariantPlan",
    "SongTask",
    "MockMusicResult",
    "RankedResult",
)


def test_required_directories_exist() -> None:
    """确保第一题要求的所有目录均存在。"""
    required = {
        "config",
        "data",
        "prompts",
        "src",
        "tests",
        "output",
        "cases",
        "logs",
    }
    missing = [name for name in sorted(required) if not (QUESTION_ROOT / name).is_dir()]
    assert not missing, f"缺少第一题目录: {missing}"


def test_required_source_files_exist() -> None:
    """确保第一题要求的所有源代码文件均存在。"""
    missing = [
        name
        for name in sorted(REQUIRED_SOURCE_FILES)
        if not (QUESTION_ROOT / "src" / name).is_file()
    ]
    assert not missing, f"缺少第一题源代码文件: {missing}"


def test_asset_directories_exist() -> None:
    """确保提示词、配置、输出和案例目录均存在。"""
    required = ("prompts", "config", "output", "cases")
    missing = [name for name in required if not (QUESTION_ROOT / name).is_dir()]
    assert not missing, f"缺少资源目录: {missing}"


def test_source_has_no_machine_specific_project_path() -> None:
    """禁止 Python 源代码包含已知的本机项目绝对路径。"""
    prohibited = "\\".join(("D:", "code4", "qiyin"))
    offenders = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in sorted((QUESTION_ROOT / "src").rglob("*.py"))
        if prohibited in path.read_text(encoding="utf-8")
    ]
    assert not offenders, f"Python 源代码包含本机绝对路径: {offenders}"


@pytest.mark.parametrize("script_name", CORE_CLI_FILES)
def test_core_cli_help(script_name: str) -> None:
    """确保所有核心命令行骨架的帮助可以离线执行。"""
    script_path = QUESTION_ROOT / "src" / script_name
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, f"{script_name} --help 执行失败: {result.stderr}"
    assert "usage:" in result.stdout


def test_workflow_contains_all_core_entities() -> None:
    """确保工作流文档定义全部核心实体。"""
    workflow = (QUESTION_ROOT / "workflow.md").read_text(encoding="utf-8")
    missing = [entity for entity in CORE_ENTITIES if entity not in workflow]
    assert not missing, f"工作流缺少核心实体: {missing}"


def test_workflow_defines_lyrics_boundaries() -> None:
    """确保工作流明确歌词任务、门禁和修改次数边界。"""
    workflow = (QUESTION_ROOT / "workflow.md").read_text(encoding="utf-8")
    assert "SongProject 不是 LyricsTask" in workflow
    assert "自动歌词修改最多一次" in workflow
    assert "只有最终 `LyricsReview.decision=accepted` 才能创建 SongTask" in workflow
    assert "第二次评估仍为 `revise` 时按 `rejected` 处理" in workflow


def test_workflow_forbids_fake_audio() -> None:
    """确保模拟结果明确不创建音频文件。"""
    workflow = (QUESTION_ROOT / "workflow.md").read_text(encoding="utf-8")
    assert "不创建 WAV 或 MP3" in workflow
    assert "is_simulated=true" in workflow
    assert "audio_path" in workflow
    assert "is_simulated=false" in workflow


def test_readme_separates_implemented_and_pending_work() -> None:
    """确保 README 不把命令行骨架描述为已完成业务。"""
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "原始趋势数据：**已实现**" in readme
    assert "**待实现，仅有 CLI 骨架**" in readme
    assert "除 `collect_trends.py` 外，其余业务脚本当前只提供 argparse CLI 骨架" in readme
