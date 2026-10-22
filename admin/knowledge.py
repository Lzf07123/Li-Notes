"""小程序速查内容导出：文章 frontmatter 是唯一内容源。"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import yaml

from admin.content import split_frontmatter

SCHEMA_VERSION = 1
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
MAX_ITEMS = 500
MAX_EXAMPLES = 20
MAX_NOTES = 30
MAX_LIST = 50
MAX_TEXT = 4000
MAX_CODE = 12000
TEXT_FIELDS = ("title", "command", "summary", "syntax")


def canonical_json(value: Any) -> str:
    """与小程序 stableStringify 保持一致的紧凑 JSON。"""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def content_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def payload_digest(payload: dict) -> str:
    """只签名业务内容，避免 generatedAt 造成同版本 Hash 漂移。"""
    signed = {
        "schemaVersion": payload.get("schemaVersion"),
        "contentVersion": payload.get("contentVersion"),
        "categories": payload.get("categories"),
        "items": payload.get("items"),
    }
    return content_sha256(signed)


def _read_frontmatter(path: Path) -> dict:
    fm_text, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    if not fm_text:
        return {}
    try:
        value = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return {}
    return value if isinstance(value, dict) else {}


def _text(value: Any, field: str, required: bool = False, max_len: int = MAX_TEXT) -> str:
    if value is None:
        value = ""
    if not isinstance(value, (str, int, float)):
        raise ValueError(f"{field} 必须是文本")
    text = str(value).strip()
    if required and not text:
        raise ValueError(f"{field} 不能为空")
    if len(text) > max_len:
        raise ValueError(f"{field} 超过 {max_len} 字符")
    if re.search(r"<\s*script\b|javascript\s*:", text, re.IGNORECASE):
        raise ValueError(f"{field} 包含可执行内容")
    return text


def _text_list(value: Any, field: str, limit: int = MAX_LIST) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} 必须是列表")
    if len(value) > limit:
        raise ValueError(f"{field} 最多 {limit} 项")
    result = []
    for item in value:
        text = _text(item, field)
        if text:
            result.append(text)
    return result


def _examples(value: Any) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_EXAMPLES:
        raise ValueError(f"examples 必须是最多 {MAX_EXAMPLES} 项的列表")
    result = []
    for index, raw in enumerate(value, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"examples[{index}] 必须是对象")
        label = _text(raw.get("label"), f"examples[{index}].label", required=True, max_len=200)
        code = _text(raw.get("code"), f"examples[{index}].code", required=True, max_len=MAX_CODE)
        result.append({"label": label, "code": code})
    return result


def normalize_config(data: Any) -> dict:
    if not isinstance(data, dict):
        raise ValueError("knowledge 配置必须是对象")
    categories = data.get("categories")
    if not isinstance(categories, list) or not categories:
        raise ValueError("knowledge.categories 必须是非空列表")
    normalized = []
    seen = set()
    for index, raw in enumerate(categories, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"categories[{index}] 必须是对象")
        category_id = _text(raw.get("id"), f"categories[{index}].id", required=True, max_len=32)
        if not CATEGORY_RE.fullmatch(category_id):
            raise ValueError(f"无效分类 id：{category_id}")
        if category_id in seen:
            raise ValueError(f"重复分类 id：{category_id}")
        seen.add(category_id)
        normalized.append(
            {
                "id": category_id,
                "label": _text(raw.get("label"), f"categories[{index}].label", required=True, max_len=40),
                "intro": _text(raw.get("intro"), f"categories[{index}].intro", max_len=120),
                "symbol": _text(raw.get("symbol"), f"categories[{index}].symbol", max_len=4),
            }
        )
    min_app_version = _text(data.get("min_app_version"), "min_app_version", max_len=32) or "0.2.0"
    return {
        "schema_version": int(data.get("schema_version") or SCHEMA_VERSION),
        "min_app_version": min_app_version,
        "categories": normalized,
    }


def load_config(root: Path) -> dict:
    path = root / "config" / "knowledge.yaml"
    if not path.exists():
        raise ValueError("缺少 config/knowledge.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return normalize_config(data)



def parse_mini_field(value: Any) -> dict:
    """读取文章 frontmatter 的 mini_json；兼容旧 dict 字段。"""
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        raise ValueError("mini_json 必须是 JSON 对象")
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"mini_json 格式错误：{exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("mini_json 必须是 JSON 对象")
    return data

def validate_mini_config(
    mini: Any,
    post_slug: str,
    post_tags: list[str] | None = None,
) -> dict:
    """校验并规范化文章内的 mini 配置；未启用时返回空对象。"""
    if mini is None:
        return {}
    if not isinstance(mini, dict):
        raise ValueError("mini 必须是 YAML 对象")
    if mini.get("enabled") is not True:
        return {"enabled": False}
    if not ID_RE.fullmatch(post_slug):
        raise ValueError("文章 slug 无效")
    raw_items = mini.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("mini.items 至少需要一个条目")
    if len(raw_items) > 100:
        raise ValueError("mini.items 最多 100 条")
    normalized = []
    seen = set()
    fallback_tags = _text_list(post_tags, "文章 tags")
    for index, raw in enumerate(raw_items, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"mini.items[{index}] 必须是对象")
        item_id = _text(raw.get("id"), f"mini.items[{index}].id", required=True, max_len=64)
        if not ID_RE.fullmatch(item_id):
            raise ValueError(f"无效速查 id：{item_id}")
        if item_id in seen:
            raise ValueError(f"重复速查 id：{item_id}")
        seen.add(item_id)
        category = _text(raw.get("category"), f"mini.items[{index}].category", required=True, max_len=32)
        if not CATEGORY_RE.fullmatch(category):
            raise ValueError(f"无效速查分类：{category}")
        examples = _examples(raw.get("examples"))
        if not examples:
            raise ValueError(f"{item_id} 至少需要一个示例")
        related = _text_list(raw.get("related"), f"{item_id}.related")
        keywords = _text_list(raw.get("keywords"), f"{item_id}.keywords")
        tags = _text_list(raw.get("tags"), f"{item_id}.tags") or fallback_tags
        item = {
            "id": item_id,
            "category": category,
            "title": _text(raw.get("title"), f"{item_id}.title", required=True, max_len=120),
            "command": _text(raw.get("command"), f"{item_id}.command", required=True, max_len=200),
            "summary": _text(raw.get("summary"), f"{item_id}.summary", required=True),
            "syntax": _text(raw.get("syntax"), f"{item_id}.syntax", required=True),
            "keywords": keywords,
            "tags": tags,
            "examples": examples,
            "notes": _text_list(raw.get("notes"), f"{item_id}.notes", limit=MAX_NOTES),
            "related": related,
        }
        source_url = _text(raw.get("source_url"), f"{item_id}.source_url", max_len=2048)
        if source_url:
            if not (source_url.startswith("/") or source_url.startswith("https://")):
                raise ValueError(f"{item_id}.source_url 只允许站内路径或 HTTPS")
            item["source_url"] = source_url
        order = raw.get("order", 0)
        try:
            item["order"] = int(order or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{item_id}.order 必须是整数") from exc
        normalized.append(item)
    return {"enabled": True, "items": normalized}


def _article_url(base_url: str, slug: str) -> str:
    path = f"posts/{slug}/"
    if base_url:
        return urljoin(base_url.rstrip("/") + "/", path)
    return f"/{path}"


def build_bundle(
    root: Path,
    base_url: str = "",
    now: dt.datetime | None = None,
) -> tuple[dict, dict, str]:
    """扫描文章并生成 (manifest, payload, canonical_data_json)。"""
    now = now or dt.datetime.now().astimezone()
    config = load_config(root)
    category_config = {item["id"]: item for item in config["categories"]}
    items: list[dict] = []
    seen_ids: set[str] = set()
    for path in sorted((root / "content" / "posts").glob("*.md")):
        if path.stem in ("_index", "index"):
            continue
        fm = _read_frontmatter(path)
        if not fm:
            continue
        if fm.get("draft") is True or str(fm.get("status") or "published") != "published":
            continue
        date_text = str(fm.get("date") or "")[:10]
        try:
            if date_text and dt.date.fromisoformat(date_text) > now.date():
                continue
        except ValueError:
            pass
        mini = validate_mini_config(
            parse_mini_field(fm.get("mini_json")), path.stem, fm.get("tags") or []
        )
        if not mini.get("enabled"):
            continue
        source_url = _article_url(base_url, path.stem)
        updated = str(fm.get("updated") or fm.get("date") or "")[:10]
        for item in mini["items"]:
            if item["id"] in seen_ids:
                raise ValueError(f"重复速查 id：{item['id']}")
            if item["category"] not in category_config:
                raise ValueError(f"{item['id']} 使用了未知分类：{item['category']}")
            seen_ids.add(item["id"])
            normalized = dict(item)
            normalized["source_url"] = normalized.get("source_url") or source_url
            normalized["source_title"] = str(fm.get("title") or path.stem)
            normalized["updated"] = updated
            items.append(normalized)
    if not items:
        raise ValueError("没有可导出的 mini 速查条目")
    for item in items:
        for related_id in item["related"]:
            if related_id not in seen_ids:
                raise ValueError(f"{item['id']} 关联了不存在的速查：{related_id}")
    order_map = {item["id"]: index for index, item in enumerate(config["categories"])}
    items.sort(key=lambda item: (order_map[item["category"]], item.get("order", 0), item["id"]))
    counts: dict[str, int] = {}
    for item in items:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    categories = [
        {**category, "count": counts.get(category["id"], 0)}
        for category in config["categories"]
        if counts.get(category["id"], 0)
    ]
    core = {"schemaVersion": SCHEMA_VERSION, "categories": categories, "items": items}
    core_hash = hashlib.sha256(canonical_json(core).encode("utf-8")).hexdigest()
    content_version = f"{now:%Y.%m.%d}.{core_hash[:8]}"
    payload = {
        **core,
        "contentVersion": content_version,
        "generatedAt": now.isoformat(timespec="seconds"),
    }
    data_text = canonical_json(payload)
    digest = payload_digest(payload)
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "contentVersion": content_version,
        "minAppVersion": config["min_app_version"],
        "generatedAt": payload["generatedAt"],
        "count": len(items),
        "sha256": digest,
        "dataUrl": f"/knowledge/{content_version}.json",
    }
    return manifest, payload, data_text


def export_bundle(
    root: Path,
    output_root: Path,
    base_url: str = "",
    now: dt.datetime | None = None,
) -> dict:
    manifest, _payload, data_text = build_bundle(root, base_url=base_url, now=now)
    knowledge_dir = output_root / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_root / manifest["dataUrl"].lstrip("/")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_tmp = data_path.with_name(data_path.name + ".tmp")
    data_tmp.write_text(data_text, encoding="utf-8")
    data_tmp.replace(data_path)
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    manifest_path = knowledge_dir / "manifest.json"
    manifest_tmp = manifest_path.with_name("manifest.json.tmp")
    manifest_tmp.write_text(manifest_text, encoding="utf-8")
    manifest_tmp.replace(manifest_path)
    for stale in knowledge_dir.glob("*.json"):
        if stale.name not in ("manifest.json", data_path.name):
            stale.unlink()
    return {**manifest, "manifestPath": str(manifest_path), "dataPath": str(data_path)}
