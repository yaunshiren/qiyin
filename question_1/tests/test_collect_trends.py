"""测试真实趋势采集模块的解析、网络错误和路径保护。"""

from __future__ import annotations

import csv
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import requests

from question_1.src import collect_trends as collector
from question_1.src.collect_trends import CSV_FIELDS, TrendCollectionError
from question_1.src.utils import ProjectPathError, resolve_project_path


TEST_WORKSPACE = Path(".tmp/test_collect_trends")
RETRIEVED_AT = "2026-07-26T08:00:00.000000Z"
RAW_RESPONSE_PATH = "question_1/data/raw_responses/sample.xml"


class _FakeResponse:
    """提供测试所需的最小 HTTP 响应对象。"""

    def __init__(self, content: bytes, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code


@pytest.fixture
def workspace() -> Iterator[Path]:
    """创建并在测试后清理项目内临时目录。"""
    absolute = resolve_project_path(TEST_WORKSPACE)
    if absolute.exists():
        shutil.rmtree(absolute)
    absolute.mkdir(parents=True)
    yield TEST_WORKSPACE
    if absolute.exists():
        shutil.rmtree(absolute)


def test_parse_normal_rss() -> None:
    """正常 RSS 应解析为字段完整的趋势记录。"""
    records = collector.parse_rss(
        _rss_document(2),
        source_url="https://example.test/rss?geo=US",
        geo="US",
        max_items=20,
        retrieved_at=RETRIEVED_AT,
        raw_response_path=RAW_RESPONSE_PATH,
    )

    assert len(records) == 2
    assert tuple(records[0]) == CSV_FIELDS
    assert records[0]["keyword"] == "趋势关键词 1"
    assert records[0]["traffic_text"] == "100K+"
    assert records[0]["description"] == "新闻摘要 1"
    assert records[0]["source_date"] == "2026-07-26T08:00:00Z"
    assert records[0]["raw_response_path"] == RAW_RESPONSE_PATH


def test_default_output_is_raw_trends_csv() -> None:
    """采集器默认输出应与后续清洗结果路径分离。"""
    assert collector.DEFAULT_OUTPUT == "question_1/data/raw_trends.csv"


def test_parse_empty_rss() -> None:
    """空 RSS 应返回空记录列表。"""
    records = collector.parse_rss(
        b"<?xml version='1.0' encoding='UTF-8'?><rss><channel></channel></rss>",
        source_url="https://example.test/rss?geo=US",
        geo="US",
        max_items=20,
        retrieved_at=RETRIEVED_AT,
        raw_response_path=RAW_RESPONSE_PATH,
    )
    assert records == []


def test_invalid_xml_raises_clear_error() -> None:
    """无效 XML 应抛出清晰的解析错误。"""
    with pytest.raises(TrendCollectionError, match="RSS XML 解析失败"):
        collector.parse_rss(
            b"<rss><channel>",
            source_url="https://example.test/rss?geo=US",
            geo="US",
            max_items=20,
            retrieved_at=RETRIEVED_AT,
            raw_response_path=RAW_RESPONSE_PATH,
        )


def test_network_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """网络超时应转换为中文采集错误。"""
    def raise_timeout(*args: Any, **kwargs: Any) -> _FakeResponse:
        raise requests.Timeout("测试超时")

    monkeypatch.setattr(collector.requests, "get", raise_timeout)
    with pytest.raises(TrendCollectionError, match="网络请求超时"):
        collector.fetch_rss("https://example.test/rss", 1)


def test_http_non_200_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP 非 200 状态应被明确拒绝。"""
    def fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse("服务器错误".encode("utf-8"), status_code=503)

    monkeypatch.setattr(collector.requests, "get", fake_get)
    with pytest.raises(TrendCollectionError, match="非 200 状态：503"):
        collector.fetch_rss("https://example.test/rss", 1)


def test_max_items_limits_records() -> None:
    """max-items 应限制解析结果数量。"""
    records = collector.parse_rss(
        _rss_document(4),
        source_url="https://example.test/rss?geo=US",
        geo="US",
        max_items=2,
        retrieved_at=RETRIEVED_AT,
        raw_response_path=RAW_RESPONSE_PATH,
    )
    assert len(records) == 2


def test_trend_id_is_stable_and_unique() -> None:
    """趋势标识应跨次解析稳定，并在结果内保持唯一。"""
    first = collector.parse_rss(
        _rss_document(3, repeated_keyword=True),
        source_url="https://example.test/rss?geo=US",
        geo="US",
        max_items=20,
        retrieved_at=RETRIEVED_AT,
        raw_response_path=RAW_RESPONSE_PATH,
    )
    second = collector.parse_rss(
        _rss_document(3, repeated_keyword=True),
        source_url="https://example.test/rss?geo=US",
        geo="US",
        max_items=20,
        retrieved_at="2026-07-26T09:00:00.000000Z",
        raw_response_path="question_1/data/raw_responses/other.xml",
    )

    first_ids = [record["trend_id"] for record in first]
    second_ids = [record["trend_id"] for record in second]
    assert len(first_ids) == len(set(first_ids))
    assert first_ids == second_ids


def test_existing_output_is_not_overwritten(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """默认模式应在网络请求前拒绝覆盖已有 CSV。"""
    config_path = _write_config(workspace)
    output_path = workspace / "raw_trends.csv"
    resolve_project_path(output_path).write_text("原有内容", encoding="utf-8")
    network_called = False

    def fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        nonlocal network_called
        network_called = True
        return _FakeResponse(_rss_document(1))

    monkeypatch.setattr(collector.requests, "get", fake_get)
    with pytest.raises(FileExistsError, match="默认禁止覆盖"):
        collector.collect_trends(
            config_path=config_path,
            output_path=output_path,
            raw_response_dir=workspace / "raw",
        )

    assert resolve_project_path(output_path).read_text(encoding="utf-8") == "原有内容"
    assert network_called is False


def test_raw_xml_and_csv_are_saved(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """成功请求应保存原始 XML 和 UTF-8 CSV。"""
    config_path = _write_config(workspace)
    xml_content = _rss_document(2)

    def fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(xml_content)

    monkeypatch.setattr(collector.requests, "get", fake_get)
    result = collector.collect_trends(
        config_path=config_path,
        output_path=workspace / "raw_trends.csv",
        raw_response_dir=workspace / "raw",
    )

    assert result.raw_response_path.read_bytes() == xml_content
    with result.output_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert len(rows) == 2
    assert tuple(rows[0]) == CSV_FIELDS
    assert rows[0]["raw_response_path"].startswith(".tmp/test_collect_trends/raw/")


def test_paths_outside_project_are_rejected(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """目录穿越输出应在发起网络请求前被拒绝。"""
    config_path = _write_config(workspace)
    network_called = False

    def fake_get(*args: Any, **kwargs: Any) -> _FakeResponse:
        nonlocal network_called
        network_called = True
        return _FakeResponse(_rss_document(1))

    monkeypatch.setattr(collector.requests, "get", fake_get)
    with pytest.raises(ProjectPathError, match="超出项目目录"):
        collector.collect_trends(
            config_path=config_path,
            output_path=Path("..") / "outside.csv",
            raw_response_dir=workspace / "raw",
        )
    assert network_called is False


def _write_config(workspace: Path) -> Path:
    """在项目内测试目录写入最小趋势源配置。"""
    config_path = workspace / "trend_sources.yaml"
    resolve_project_path(config_path).write_text(
        "\n".join(
            (
                "provider: google_trends_rss",
                "enabled: true",
                "geo: US",
                "timeout_seconds: 2",
                "max_items: 20",
                'rss_url_template: "https://example.test/rss?geo={geo}"',
                "",
            )
        ),
        encoding="utf-8",
    )
    return config_path


def _rss_document(count: int, *, repeated_keyword: bool = False) -> bytes:
    """构建固定且不访问网络的 RSS 测试数据。"""
    items = []
    for index in range(1, count + 1):
        keyword = "重复关键词" if repeated_keyword else f"趋势关键词 {index}"
        items.append(
            f"""
            <item>
              <title>{keyword}</title>
              <link>https://example.test/story/{index}</link>
              <pubDate>Sun, 26 Jul 2026 08:00:00 GMT</pubDate>
              <ht:approx_traffic>{index}00K+</ht:approx_traffic>
              <ht:news_item>
                <ht:news_item_snippet>新闻摘要 {index}</ht:news_item_snippet>
              </ht:news_item>
            </item>
            """
        )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss xmlns:ht="https://trends.google.com/trending/rss">
      <channel>{''.join(items)}</channel>
    </rss>
    """
    return xml.encode("utf-8")
