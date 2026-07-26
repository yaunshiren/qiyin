"""从配置的 Google Trends RSS 采集真实趋势数据。"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from xml.etree import ElementTree

import requests

if __package__:
    from .utils import (
        ProjectPathError,
        ensure_project_directory,
        load_yaml,
        prepare_output_path,
        project_relative_path,
        resolve_project_path,
        utc_now_iso,
        write_project_bytes,
        write_utf8_csv,
    )
else:
    from utils import (
        ProjectPathError,
        ensure_project_directory,
        load_yaml,
        prepare_output_path,
        project_relative_path,
        resolve_project_path,
        utc_now_iso,
        write_project_bytes,
        write_utf8_csv,
    )


DEFAULT_CONFIG = "question_1/config/trend_sources.yaml"
DEFAULT_OUTPUT = "question_1/data/raw_trends.csv"
DEFAULT_RAW_RESPONSE_DIR = "question_1/data/raw_responses"
USER_AGENT = "qiyin-ai-music-workflow/0.1 (educational RSS client)"
CSV_FIELDS = (
    "trend_id",
    "keyword",
    "source",
    "source_url",
    "source_date",
    "traffic_text",
    "description",
    "retrieved_at",
    "raw_response_path",
)


class TrendCollectionError(RuntimeError):
    """表示趋势配置、网络请求或 RSS 解析失败。"""


@dataclass(frozen=True)
class CollectionResult:
    """保存一次趋势采集的输出摘要。"""

    output_path: Path
    raw_response_path: Path
    item_count: int


def build_parser() -> argparse.ArgumentParser:
    """构建趋势采集命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="从 Google Trends RSS 采集真实趋势数据。")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="项目内趋势源 YAML 配置路径。")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="项目内 UTF-8 CSV 输出路径。")
    parser.add_argument(
        "--raw-response-dir",
        default=DEFAULT_RAW_RESPONSE_DIR,
        help="项目内原始 XML 保存目录。",
    )
    parser.add_argument("--geo", help="覆盖配置中的地区代码，例如 US。")
    parser.add_argument("--max-items", type=int, help="覆盖配置中的最大趋势条数。")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有 CSV 输出。")
    return parser


def fetch_rss(source_url: str, timeout_seconds: float) -> bytes:
    """请求 RSS 地址，并在超时或 HTTP 错误时抛出清晰异常。"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8",
    }
    try:
        response = requests.get(
            source_url,
            headers=headers,
            timeout=(timeout_seconds, timeout_seconds),
            allow_redirects=True,
        )
    except requests.Timeout as exc:
        raise TrendCollectionError(f"网络请求超时：{source_url}") from exc
    except requests.RequestException as exc:
        raise TrendCollectionError(f"网络请求失败：{source_url}；{exc}") from exc

    if response.status_code != 200:
        raise TrendCollectionError(f"网络请求返回非 200 状态：{response.status_code}；{source_url}")
    return response.content


def parse_rss(
    xml_content: bytes,
    *,
    source_url: str,
    geo: str,
    max_items: int,
    retrieved_at: str,
    raw_response_path: str,
) -> list[dict[str, str]]:
    """解析 Google Trends RSS，并返回字段完整且标识稳定的趋势记录。"""
    if max_items <= 0:
        raise TrendCollectionError("max-items 必须大于 0。")
    try:
        root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as exc:
        raise TrendCollectionError(f"RSS XML 解析失败：{exc}") from exc

    records: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for item in (element for element in root.iter() if _local_name(element.tag) == "item"):
        keyword = _first_text(item, "title")
        if not keyword:
            continue
        source_date = _normalise_source_date(_first_text(item, "pubDate"))
        item_source_url = (
            _first_text(item, "link")
            or _first_text(item, "news_item_url")
            or source_url
        )
        traffic_text = _first_text(item, "approx_traffic")
        description = (
            _first_text(item, "description")
            or _first_text(item, "news_item_snippet")
            or _first_text(item, "news_item_title")
        )
        trend_id = _build_trend_id(
            keyword=keyword,
            source_url=item_source_url,
            source_date=source_date,
            geo=geo,
        )
        if trend_id in seen_ids:
            continue
        seen_ids.add(trend_id)
        records.append(
            {
                "trend_id": trend_id,
                "keyword": keyword,
                "source": "google_trends_rss",
                "source_url": item_source_url,
                "source_date": source_date,
                "traffic_text": traffic_text,
                "description": description,
                "retrieved_at": retrieved_at,
                "raw_response_path": raw_response_path,
            }
        )
        if len(records) >= max_items:
            break
    return records


def collect_trends(
    *,
    config_path: str | Path = DEFAULT_CONFIG,
    output_path: str | Path = DEFAULT_OUTPUT,
    raw_response_dir: str | Path = DEFAULT_RAW_RESPONSE_DIR,
    geo_override: str | None = None,
    max_items_override: int | None = None,
    overwrite: bool = False,
) -> CollectionResult:
    """执行配置校验、真实网络请求、原始响应保存和 CSV 输出。"""
    config = _validate_config(load_yaml(config_path))
    output = resolve_project_path(output_path)
    prepare_output_path(output_path, overwrite=overwrite)
    raw_directory = ensure_project_directory(raw_response_dir)

    geo = _normalise_geo(geo_override or str(config["geo"]))
    max_items = max_items_override if max_items_override is not None else int(config["max_items"])
    if max_items <= 0:
        raise TrendCollectionError("max-items 必须大于 0。")
    timeout_seconds = float(config["timeout_seconds"])
    template = str(config["rss_url_template"])
    try:
        source_url = template.format(geo=quote(geo, safe=""))
    except (KeyError, ValueError) as exc:
        raise TrendCollectionError("rss_url_template 只能使用 {geo} 占位符。") from exc

    xml_content = fetch_rss(source_url, timeout_seconds)
    retrieved_at = utc_now_iso()
    timestamp_token = re.sub(r"[^0-9]", "", retrieved_at)
    raw_filename = f"google_trends_rss_{geo}_{timestamp_token}.xml"
    raw_path = raw_directory / raw_filename
    raw_relative_path = project_relative_path(raw_path)
    write_project_bytes(raw_relative_path, xml_content)

    records = parse_rss(
        xml_content,
        source_url=source_url,
        geo=geo,
        max_items=max_items,
        retrieved_at=retrieved_at,
        raw_response_path=raw_relative_path,
    )
    write_utf8_csv(output_path, records, CSV_FIELDS, overwrite=overwrite)
    return CollectionResult(
        output_path=output,
        raw_response_path=raw_path,
        item_count=len(records),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """解析命令行参数，执行采集并输出结果摘要。"""
    args = build_parser().parse_args(argv)
    try:
        result = collect_trends(
            config_path=args.config,
            output_path=args.output,
            raw_response_dir=args.raw_response_dir,
            geo_override=args.geo,
            max_items_override=args.max_items,
            overwrite=args.overwrite,
        )
    except (
        FileExistsError,
        FileNotFoundError,
        IsADirectoryError,
        NotADirectoryError,
        ProjectPathError,
        TrendCollectionError,
        ValueError,
    ) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(f"采集完成：{result.item_count} 条趋势。")
    print(f"CSV：{project_relative_path(result.output_path)}")
    print(f"原始 XML：{project_relative_path(result.raw_response_path)}")
    return 0


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """校验趋势源配置并返回原字典。"""
    required = {"provider", "enabled", "geo", "timeout_seconds", "max_items", "rss_url_template"}
    missing = sorted(required.difference(config))
    if missing:
        raise TrendCollectionError(f"趋势源配置缺少字段：{missing}")
    if config["provider"] != "google_trends_rss":
        raise TrendCollectionError(f"不支持的趋势源：{config['provider']}")
    if config["enabled"] is not True:
        raise TrendCollectionError("趋势源未启用。")
    if isinstance(config["timeout_seconds"], bool) or not isinstance(
        config["timeout_seconds"], (int, float)
    ):
        raise TrendCollectionError("timeout_seconds 必须是数字。")
    if float(config["timeout_seconds"]) <= 0:
        raise TrendCollectionError("timeout_seconds 必须大于 0。")
    if isinstance(config["max_items"], bool) or not isinstance(config["max_items"], int):
        raise TrendCollectionError("max_items 必须是整数。")
    if int(config["max_items"]) <= 0:
        raise TrendCollectionError("max_items 必须大于 0。")
    template = config["rss_url_template"]
    if not isinstance(template, str) or "{geo}" not in template:
        raise TrendCollectionError("rss_url_template 必须包含 {geo} 占位符。")
    return config


def _normalise_geo(geo: str) -> str:
    """校验并标准化两位地区代码。"""
    normalised = geo.strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", normalised):
        raise TrendCollectionError(f"地区代码必须是两个英文字母：{geo}")
    return normalised


def _local_name(tag: str) -> str:
    """返回去除 XML 命名空间后的标签名。"""
    return tag.rsplit("}", 1)[-1]


def _clean_text(value: str | None) -> str:
    """解码实体并压缩文本中的空白。"""
    return " ".join(html.unescape(value or "").split())


def _first_text(element: ElementTree.Element, local_name: str) -> str:
    """按本地标签名返回元素后代中的第一个非空文本。"""
    for child in element.iter():
        if child is element or _local_name(child.tag) != local_name:
            continue
        value = _clean_text(child.text)
        if value:
            return value
    return ""


def _normalise_source_date(value: str) -> str:
    """尽可能将 RSS 日期转换为 UTC ISO 字符串。"""
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _build_trend_id(*, keyword: str, source_url: str, source_date: str, geo: str) -> str:
    """根据稳定来源字段生成唯一趋势标识。"""
    canonical = "\x1f".join(
        (
            "google_trends_rss",
            geo,
            keyword.casefold(),
            source_date,
            source_url,
        )
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    return f"gtr_{digest}"


if __name__ == "__main__":
    raise SystemExit(main())
