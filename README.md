# AI 音乐自动化生产工作流作业

## 1. 项目简介

本项目用于完成 AI 音乐自动化生产工作流作业。当前优先搭建第一题的工程骨架、规则和测试，不包含趋势评分、选题生成、歌曲生成或真实平台/API 集成。

## 2. 目录结构

```text
.
├── AGENTS.md
├── README.md
├── requirements.txt
├── .gitignore
└── question_1/
    ├── workflow.md
    ├── config/
    ├── data/
    ├── prompts/
    ├── src/
    ├── tests/
    ├── output/
    ├── cases/
    └── logs/
```

## 3. Python 环境

- 要求 Python 3.10 或更高版本。
- 推荐使用项目根目录下的 `.conda-env` Conda 环境。
- 不应将项目依赖安装到全局 Python 环境。

## 4. 安装依赖

在 Windows CMD 中：

```cmd
set "CONDA_ENVS_PATH=%CD%\.conda-envs"
set "CONDA_PKGS_DIRS=%CD%\.conda-pkgs"
set "CONDA_REGISTER_ENVS=false"
conda create --prefix "%CD%\.conda-env" python=3.11 -y
conda activate "%CD%\.conda-env"
python -m pip install --no-cache-dir -r requirements.txt
```

第一阶段依赖仅包括 pandas、PyYAML 和 pytest。

## 5. 第一题运行流程

以下业务命令均为**待实现**，当前脚本只提供 argparse 占位入口：

1. 准备趋势数据：待实现（`prepare_trends.py`）
2. 构建选题：待实现（`build_topics.py`）
3. 构建任务：待实现（`build_tasks.py`）
4. 模拟生成：待实现（`mock_generator.py`）
5. 执行任务：待实现（`run_tasks.py`）
6. 结果评分：待实现（`score_results.py`）

结构测试命令：

```cmd
.conda-env\python.exe -m pytest
```

## 6. 输入与输出

- 输入数据计划放在 `question_1/data/`。
- 配置放在 `question_1/config/`。
- Prompt 模板计划以 YAML 格式放在 `question_1/prompts/`。
- 详细任务元数据计划以 JSON 格式保存。
- 生成结果计划放在 `question_1/output/`。
- 典型案例计划放在 `question_1/cases/`。
- 运行日志计划放在 `question_1/logs/`。

具体文件格式和字段：待实现。

## 7. 模拟数据说明

后续模拟数据必须使用固定随机种子，以保证结果可复现。模拟评分只用于演示工作流，不代表真实音乐听感、艺术质量或商业表现。当前尚未生成模拟数据。

## 8. AI 工具参与说明

AI 工具用于辅助工程结构设计、代码草拟、文档整理和测试建议。后续若生成 Prompt、任务或模拟结果，应在相应产物中保留必要的来源与过程说明。

## 9. 人工判断与验证说明

目录规范、任务字段、Prompt 内容和评分解释需要人工复核。任何涉及音乐质量、平台趋势或业务效果的结论，都不能仅凭模拟数据直接认定。

## 10. 当前限制

- 趋势评分与歌曲生成业务逻辑尚未实现。
- 默认流程不依赖网络或真实商业 API。
- 不包含平台爬虫、音频分析库、数据库、Web 框架或前端项目。
- 当前测试仅验证项目结构和绝对路径约束。
