# AI 音乐自动化生产工作流作业

## 1. 项目简介

本项目用于完成 AI 音乐自动化生产工作流作业。完整闭环包括：真实趋势采集、趋势清洗和风险过滤、SongProject 生成、LyricsTask 构建、歌词生成与评审、最多一次自动修改、SongVariantPlan 生成、SongTask 构建、音乐结果模拟、机器排序和人工选择。

当前阶段只实现“项目范围同步 + Google Trends Trending Now RSS 网络趋势采集”。DeepSeek、任务生成、模拟生成和评分逻辑均为后续阶段内容。

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
    │   └── trend_sources.yaml
    ├── data/
    │   ├── raw_trends.csv
    │   ├── trends.csv（待趋势清洗模块生成）
    │   └── raw_responses/
    ├── prompts/
    ├── src/
    │   ├── collect_trends.py
    │   ├── prepare_trends.py
    │   ├── build_topics.py
    │   ├── build_tasks.py
    │   ├── run_tasks.py
    │   ├── review_lyrics.py
    │   ├── build_song_variants.py
    │   ├── mock_generator.py
    │   ├── score_results.py
    │   └── llm_client.py
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

依赖版本固定在 `requirements.txt`。本阶段网络采集使用 requests，RSS XML 使用 Python 标准库解析，不使用浏览器自动化工具。

## 5. 第一题运行流程

完整工作流及状态：

1. 从真实网络采集原始趋势数据：**已实现**（`collect_trends.py`）
2. 自动清洗趋势、计算机器预评分并过滤风险：**待实现**（`prepare_trends.py`）
3. 使用 DeepSeek 生成包含 LyricBrief 的 SongProject：**待实现，仅有 CLI 骨架**（`build_topics.py`）
4. 由 Python 校验 SongProject 并构建 LyricsTask：**待实现，仅有 CLI 骨架**（`build_tasks.py`）
5. 使用 DeepSeek 执行 LyricsTask 并生成 LyricsResult：**待实现，仅有 CLI 骨架**（`run_tasks.py`）
6. 使用 DeepSeek 生成结构化 LyricsReview：**待实现，仅有 CLI 骨架**（`review_lyrics.py`）
7. 对需要修改的歌词最多自动修改一次并再次评估：**待实现，仅有 CLI 骨架**（`review_lyrics.py`）
8. 使用 DeepSeek 根据 accepted 歌词生成 SongVariantPlan：**待实现，仅有 CLI 骨架**（`build_song_variants.py`）
9. 由 Python 校验版本方案并创建正式 SongTask：**待实现，仅有 CLI 骨架**（`build_tasks.py`）
10. 模拟音乐模型返回 MockMusicResult，不创建音频：**待实现，仅有 CLI 骨架**（`mock_generator.py`）
11. 对模拟结果评分排序并生成 RankedResult：**待实现，仅有 CLI 骨架**（`score_results.py`）
12. 人工选择最终案例：**待实现**

除 `collect_trends.py` 外，其余业务脚本当前只提供 argparse CLI 骨架，不代表业务功能已经完成。`llm_client.py` 只预留后续 DeepSeek 统一封装，本阶段不发起任何模型请求。

网络采集命令：

```cmd
.conda-env\python.exe question_1\src\collect_trends.py --config question_1\config\trend_sources.yaml --output question_1\data\raw_trends.csv --raw-response-dir question_1\data\raw_responses
```

默认不覆盖已有 CSV；确认覆盖时显式添加 `--overwrite`。网络请求失败时程序返回清晰错误，不生成伪造数据。网络源、地区、超时和数量限制由 YAML 配置管理。

测试命令：

```cmd
.conda-env\python.exe -m pytest -p no:cacheprovider
```

## 6. 输入与输出

- 趋势源配置保存在 `question_1/config/trend_sources.yaml`，不包含认证信息。
- 采集器将未经清洗的趋势 CSV 默认输出到 `question_1/data/raw_trends.csv`。
- `prepare_trends.py` 后续将清洗后的趋势输出到 `question_1/data/trends.csv`，当前尚未实现。
- 每次成功 HTTP 响应的原始 XML 保存在 `question_1/data/raw_responses/`。
- Prompt 模板计划以 YAML 格式放在 `question_1/prompts/`。
- 详细任务元数据计划以 JSON 格式保存。
- SongProject、LyricsTask、LyricsResult、LyricsReview、SongVariantPlan、SongTask、MockMusicResult 和 RankedResult 计划按类型保存在 `question_1/output/` 的相对路径子目录中。
- 典型案例计划放在 `question_1/cases/`。
- 运行日志计划放在 `question_1/logs/`。

趋势 CSV 包含 `trend_id`、`keyword`、`source`、`source_url`、`source_date`、`traffic_text`、`description`、`retrieved_at` 和 `raw_response_path`。网络不可用时，已保存的原始 XML 可用于复现后续清洗流程。

## 7. 模拟数据说明

后续音乐生成阶段只模拟 MockMusicResult：必须满足 `is_simulated=true` 且 `audio_path` 为空，不创建 WAV、MP3 或其他虚假音频。真实 DeepSeek 歌词调用生成的 LyricsResult 必须满足 `is_simulated=false`。模拟数据使用固定随机种子；模拟评分不代表真实音乐听感、艺术质量或商业表现。

## 8. AI 工具参与说明

AI 工具用于辅助工程结构设计、代码草拟、文档整理和测试建议。DeepSeek 将在后续阶段负责创意文本、歌词、歌词评审和歌曲版本创意；Python 负责 JSON 校验、稳定 ID、安全路径、状态、重试、任务清单和确定性评分。本阶段不实现 DeepSeek 调用，所有 API Key 必须通过环境变量提供。

## 9. 人工判断与验证说明

网络源配置、趋势字段、提示词、任务元数据和评分解释都需要人工复核。只有最终 `LyricsReview.decision=accepted` 的歌词才能创建 SongTask。DeepSeek 的歌词评审不代表专业作词人、真实听众或市场评价；最终案例必须由人工选择。

## 10. 当前限制

- 当前网络趋势采集依赖 Google Trends RSS 的可用性和响应格式。
- 不进行网页自动化、浏览器爬虫或平台页面抓取。
- DeepSeek、趋势清洗和预评分、歌词生命周期、任务生成、模拟结果和排序逻辑尚未实现；相应 CLI 只是骨架。
- 不创建音频文件，不包含音频分析库、数据库、Web 框架或前端项目。
