# 第一题完整工作流

## 当前实现范围

当前只实现 Google Trends Trending Now RSS 真实网络采集。网络源由 YAML 配置管理，成功响应保存为项目内原始 XML，并输出 UTF-8 CSV。其余模块只有职责明确的 argparse CLI 骨架，不包含 DeepSeek 调用、趋势算法、歌词生成、歌词评审、任务生成、音乐模拟或评分业务逻辑。

## 十二步工作流

1. 从真实网络采集原始趋势数据，形成 TrendRecord（已实现）。
2. 自动清洗趋势、计算机器预评分并过滤风险（待实现）。
3. 使用 DeepSeek 生成 SongProject，包括歌曲主题、LyricBrief 和初步音乐方向（待实现）。
4. 由 Python 校验 SongProject，并根据 LyricBrief 构建 LyricsTask（待实现）。
5. 使用 DeepSeek 执行 LyricsTask，生成 LyricsResult（待实现）。
6. 使用 DeepSeek 生成结构化 LyricsReview（待实现）。
7. 对 decision=revise 的歌词最多自动修改一次，并再次评估（待实现）。
8. 使用 DeepSeek 根据最终 accepted 歌词生成 SongVariantPlan（待实现）。
9. 由 Python 校验版本方案并创建正式 SongTask（待实现）。
10. 模拟音乐模型返回 MockMusicResult，不创建任何音频（待实现）。
11. 对 MockMusicResult 进行确定性评分和排序，生成 RankedResult（待实现）。
12. 由人工选择最终案例（待实现）。

## 核心实体及关系

实体关系为：

`TrendRecord → SongProject（内含 LyricBrief）→ LyricsTask → LyricsResult → LyricsReview → SongVariantPlan → SongTask → MockMusicResult → RankedResult → 人工选择`

- **TrendRecord**：真实趋势记录。必要字段包括 `trend_id`、`keyword`、`source`、`source_url`、`source_date`、`traffic_text`、`description`、`retrieved_at` 和 `raw_response_path`。
- **SongProject**：歌曲创意方案。必要字段包括 `song_project_id`、来源趋势 ID、歌曲主题、创意角度、`lyric_brief`、初步音乐方向、状态和创建时间。**SongProject 不是 LyricsTask**。
- **LyricBrief**：SongProject 内部的歌词创作简报。必要字段包括语言、受众、叙事视角、情绪、叙事弧线、主钩子目标、段落要求和创作限制。
- **LyricsTask**：Python 根据已校验 SongProject 和 LyricBrief 构建的可执行任务记录。必要字段包括 `lyrics_task_id`、`song_project_id`、LyricBrief 快照、尝试次数、状态和创建时间。
- **LyricsResult**：执行 LyricsTask 后得到的结构化歌词。必要字段包括 `lyrics_result_id`、`lyrics_task_id`、结构化歌词段落、模型信息、尝试次数、`is_simulated` 和创建时间。真实 DeepSeek 调用时必须 `is_simulated=false`。
- **LyricsReview**：针对 LyricsResult 的结构化评审。必要字段包括 `review_id`、`lyrics_result_id`、六项评分、`lyrics_score`、`risk_pass`、`decision`、问题列表、修改建议和评审轮次。
- **SongVariantPlan**：基于最终 accepted 歌词的歌曲版本创意方案。必要字段包括 `variant_plan_id`、`song_project_id`、`lyrics_result_id`、`lyrics_review_id` 和多个结构化版本方向。
- **SongTask**：Python 校验 SongVariantPlan 后创建的正式音乐任务。必要字段包括 `song_task_id`、版本方案 ID、最终歌词结果 ID、结构化音乐参数、状态和创建时间。
- **MockMusicResult**：SongTask 的模拟音乐模型返回。必要字段包括 `mock_result_id`、`song_task_id`、模拟元数据、`is_simulated=true`、空字符串 `audio_path` 和创建时间。
- **RankedResult**：MockMusicResult 的确定性评分与排名记录。必要字段包括 `ranked_result_id`、`mock_result_id`、分项分数、总分、排名和说明。

SongProject 是创意方案，LyricBrief 是其内部简报；LyricsTask 是 Python 构建的可执行记录，三者不可混用。

## DeepSeek 与 Python 的职责

DeepSeek 后续负责：

- 生成 SongProject 中的创意文本、主题和 LyricBrief；
- 执行 LyricsTask 并生成歌词；
- 生成结构化 LyricsReview；
- 按修改建议最多重写一次歌词；
- 根据 accepted 歌词生成 SongVariantPlan。

Python 后续负责：

- JSON 结构和必填字段校验；
- 稳定 ID、安全相对路径和 UTF-8 文件写入；
- 状态流转、尝试次数和最多一次修改限制；
- LyricsTask、SongTask 等任务清单；
- accepted 门禁、失败处理和确定性评分排序。

本阶段 `llm_client.py` 只提供 CLI 骨架，不调用 DeepSeek 或其他外部 API。所有 API Key 必须来自环境变量。

## 模块职责

| 模块 | 唯一职责 | 当前状态 |
|---|---|---|
| `collect_trends.py` | 采集真实网络趋势并保存原始 XML 和 CSV | 已实现 |
| `prepare_trends.py` | 趋势清洗、机器预评分和风险过滤 | CLI 骨架，待实现 |
| `build_topics.py` | 使用 DeepSeek 生成 SongProject，不生成完整歌词 | CLI 骨架，待实现 |
| `build_tasks.py` | 由 Python 创建 LyricsTask，并仅为 accepted 歌词创建 SongTask | CLI 骨架，待实现 |
| `run_tasks.py` | 执行 LyricsTask 并生成 LyricsResult | CLI 骨架，待实现 |
| `review_lyrics.py` | 生成 LyricsReview，管理最多一次自动修改和再次评估 | CLI 骨架，待实现 |
| `build_song_variants.py` | 根据 accepted 歌词生成 SongVariantPlan | CLI 骨架，待实现 |
| `mock_generator.py` | 只模拟 SongTask 的 MockMusicResult | CLI 骨架，待实现 |
| `score_results.py` | 只评分 MockMusicResult 并生成 RankedResult | CLI 骨架，待实现 |
| `llm_client.py` | 后续统一封装 DeepSeek 请求、错误和重试 | CLI 骨架，待实现 |

## 状态流转

建议状态链为：

`SongProject:drafted → validated/rejected → LyricsTask:pending → running → completed/failed → LyricsReview:accepted/revise/rejected → SongVariantPlan:drafted → validated/rejected → SongTask:ready → MockMusicResult:completed → RankedResult:ranked → human_selected/not_selected`

只有最终 `LyricsReview.decision=accepted` 才能创建 SongTask。任何风险校验失败、结构校验失败或歌词最终被拒绝的记录都不得进入 SongTask 阶段。

## 歌词评分与决策规则

歌词评分公式为：

```text
lyrics_score =
    structure_score * 0.20
    + theme_alignment_score * 0.20
    + hook_score * 0.20
    + singability_score * 0.20
    + language_naturalness_score * 0.10
    + originality_score * 0.10
```

决策规则：

- `risk_pass=false`：`rejected`；
- `lyrics_score >= 80`：`accepted`；
- `70 <= lyrics_score < 80`：`revise`；
- `lyrics_score < 70`：`rejected`；
- 第二次评估仍为 `revise` 时按 `rejected` 处理。

DeepSeek 的 LyricsReview 只用于工作流内结构化筛选，不代表专业作词人、真实听众或市场评价。

## 歌词修改规则

- 自动歌词修改最多一次。
- 第一次评审为 revise 时，Python 才能创建一次修改尝试。
- 修改后的 LyricsResult 必须使用新的稳定 ID，并将尝试次数记录为 2。
- 第二次评估只能得到 accepted 或 rejected；若模型仍返回 revise，Python 必须转换为 rejected。
- rejected 歌词不得生成 SongVariantPlan 或 SongTask。

## 输出目录

所有输出都使用项目内相对路径：

- `question_1/data/raw_trends.csv`：采集器输出的未经清洗 TrendRecord CSV；
- `question_1/data/trends.csv`：`prepare_trends.py` 后续输出的清洗、预评分和风险过滤结果；
- `question_1/data/raw_responses/`：真实网络请求的原始 XML；
- `question_1/output/song_projects/`：SongProject JSON；
- `question_1/output/lyrics_tasks/`：LyricsTask JSON；
- `question_1/output/lyrics_results/`：LyricsResult JSON；
- `question_1/output/lyrics_reviews/`：LyricsReview JSON；
- `question_1/output/song_variant_plans/`：SongVariantPlan JSON；
- `question_1/output/song_tasks/`：SongTask JSON；
- `question_1/output/mock_music_results/`：MockMusicResult JSON；
- `question_1/output/ranked_results/`：RankedResult JSON；
- `question_1/cases/`：人工最终选择案例。

## 网络、模拟方法及限制

- 原型趋势源为 Google Trends Trending Now RSS，不进行网页自动化或浏览器爬虫。
- 网络失败时不得伪造成功数据；可使用已保存的原始 XML 复现后续离线流程。
- MockMusicResult 必须 `is_simulated=true`，`audio_path` 必须为空，不创建 WAV 或 MP3。
- LyricsResult 在真实 DeepSeek 调用时必须 `is_simulated=false`。
- 模拟数据必须使用固定随机种子，模拟评分不得解释为真实听感、专业评价或市场表现。
