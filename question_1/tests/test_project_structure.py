"""验证项目初始骨架。"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUESTION_ROOT = PROJECT_ROOT / "question_1"


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
    required = {
        "__init__.py",
        "prepare_trends.py",
        "build_topics.py",
        "build_tasks.py",
        "mock_generator.py",
        "run_tasks.py",
        "score_results.py",
        "utils.py",
    }
    missing = [name for name in sorted(required) if not (QUESTION_ROOT / "src" / name).is_file()]
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
