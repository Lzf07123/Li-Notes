"""文章批量导入：多选 Markdown 或 ZIP，统一写入 content/posts 并返回统计。"""

import io
import hashlib
import json
import re
import unicodedata
import zipfile
from datetime import date, datetime
from pathlib import PurePosixPath

import yaml

from admin import content, knowledge as knowledge_store
from admin.config import settings

MD_SUFFIXES = (".md", ".markdown")
SKIP_STEMS = {"_index", "index"}
VALID_STATUSES = {"published", "draft"}
MAX_TITLE_LENGTH = 200
MAX_SUMMARY_LENGTH = 1000
MAX_TAGS = 50
MAX_TAG_LENGTH = 64
TEMPLATE_KINDS = {
    "note": "linotes-note-template.md",
    "mini": "linotes-mini-sync-template.md",
}


def _plain_text(
    value,
    field: str,
    filename: str,
    *,
    required: bool = False,
    max_length: int = 4000,
) -> str:
    if value is None:
        value = ""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{filename}: {field} 必须是文本")
    text = str(value).strip()
    if required and not text:
        raise ValueError(f"{filename}: {field} 不能为空")
    if len(text) > max_length:
        raise ValueError(f"{filename}: {field} 超过 {max_length} 字符")
    return text


def _normalize_date(value, filename: str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _plain_text(value, "date", filename, required=True, max_length=40)
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise ValueError(f"{filename}: date 必须是 YYYY-MM-DD 格式") from exc


def _normalize_status(value, filename: str) -> str:
    status = _plain_text(
        value if value is not None else "published",
        "status",
        filename,
        required=True,
        max_length=20,
    ).lower()
    if status not in VALID_STATUSES:
        raise ValueError(f"{filename}: status 仅支持 published 或 draft")
    return status


def _normalize_tags(value, filename: str) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    elif isinstance(value, list):
        raw_items = value
    else:
        raise ValueError(f"{filename}: tags 必须是列表或用逗号分隔的文本")
    if len(raw_items) > MAX_TAGS:
        raise ValueError(f"{filename}: tags 最多 {MAX_TAGS} 项")
    tags: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        tag = _plain_text(item, "tags", filename, max_length=MAX_TAG_LENGTH)
        key = tag.casefold()
        if tag and key not in seen:
            seen.add(key)
            tags.append(tag)
    return tags


def _normalize_bool(value, field: str, filename: str) -> bool:
    if isinstance(value, bool):
        return value
    text = _plain_text(value, field, filename, required=True, max_length=10).lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"{filename}: {field} 必须是 true 或 false")


def _normalize_mini(fm: dict, slug: str, filename: str) -> None:
    raw = fm.get("mini_json")
    if raw in (None, ""):
        return
    try:
        mini = knowledge_store.parse_mini_field(raw)
        normalized = knowledge_store.validate_mini_config(
            mini, slug, fm.get("tags") or []
        )
    except ValueError as exc:
        raise ValueError(f"{filename}: mini_json 校验失败：{exc}") from exc
    fm["mini_json"] = json.dumps(normalized, ensure_ascii=False, indent=2)


def template_markdown(kind: str, today: date | None = None) -> str:
    """生成可直接编辑并导入的 Markdown 模板。"""
    if kind not in TEMPLATE_KINDS:
        raise ValueError("未知模板类型")
    day = (today or date.today()).isoformat()
    if kind == "note":
        return f"""---
title: "示例：我的学习笔记"
slug: imported-note-example
date: {day}
status: draft
tags:
  - linux
  - command
summary: "一句话说明这篇笔记解决了什么问题。"
cover: ""
pinned: false
---

# 示例：我的学习笔记

## 今天学了什么

用一两句话说明主题、使用场景和前置条件。

## 操作步骤

1. 写下关键步骤。
2. 给出可复现的命令或配置。
3. 记录验证结果和容易出错的地方。

## 小结

写下这次练习真正掌握了什么。
"""
    mini = {
        "enabled": True,
        "items": [
            {
                "id": "mini-sync-example",
                "category": "linux",
                "title": "示例：更新软件源索引",
                "command": "apt update",
                "summary": "刷新 Debian / Ubuntu 的软件包索引。",
                "keywords": ["更新", "软件源", "apt"],
                "tags": ["Linux", "包管理"],
                "syntax": "sudo apt update",
                "examples": [
                    {
                        "label": "刷新软件源索引",
                        "code": "sudo apt update",
                    }
                ],
                "notes": ["安装或升级软件包前先执行。"],
                "related": [],
                "order": 10,
            }
        ],
    }
    mini_json = json.dumps(mini, ensure_ascii=False, indent=2)
    indented_mini = "\n".join(f"  {line}" for line in mini_json.splitlines())
    return f"""---
title: "示例：小程序同步速查"
slug: mini-sync-example
date: {day}
status: draft
tags:
  - linux
  - command
summary: "演示如何把一篇笔记同步为小程序速查条目。"
cover: ""
pinned: false
mini_json: |-
{indented_mini}
---

# 示例：小程序同步速查

## 命令速查

| 命令 | 作用 |
| --- | --- |
| `sudo apt update` | 刷新软件源索引 |

## 说明

发布文章后，后台构建会读取 `mini_json` 并生成小程序 manifest。
"""


def parse_document(filename: str, text: str) -> tuple[str, dict, str]:
    """解析单个 Markdown 文档，返回 (slug, frontmatter, body)。"""
    fm_text, body = content.split_frontmatter(text)
    if fm_text:
        try:
            fm = yaml.safe_load(fm_text) or {}
        except ValueError as exc:
            detail = str(exc).lower()
            if "month must be" in detail or "day is out of range" in detail:
                raise ValueError(f"{filename}: date 必须是 YYYY-MM-DD 格式") from exc
            raise ValueError(f"{filename}: frontmatter 解析失败：{exc}") from exc
        except yaml.YAMLError as exc:
            raise ValueError(f"{filename}: frontmatter 解析失败") from exc
        body = body.lstrip("\n")
    else:
        fm, body = {}, text
    if not isinstance(fm, dict):
        raise ValueError(f"{filename}: frontmatter 必须是键值对")
    security_errors = content.scan_markdown_security(body)
    if security_errors:
        raise ValueError(f"{filename}: 正文包含不安全 HTML：{security_errors[0]}")
    explicit = str(fm.pop("slug", "")).strip("/")
    if fm.get("date") not in (None, ""):
        fm["date"] = _normalize_date(fm["date"], filename)
    fm["status"] = _normalize_status(fm.get("status"), filename)
    fm["tags"] = _normalize_tags(fm.get("tags"), filename)
    if "title" in fm:
        fm["title"] = _plain_text(
            fm["title"],
            "title",
            filename,
            max_length=MAX_TITLE_LENGTH,
        )
        if not fm["title"]:
            fm.pop("title")
    stem = PurePosixPath(filename).stem
    slug = _resolve_slug(explicit, stem, fm.get("title", ""), filename)
    if not fm.get("title"):
        fm["title"] = _infer_title(stem, body)
    fm["title"] = _plain_text(
        fm["title"],
        "title",
        filename,
        required=True,
        max_length=MAX_TITLE_LENGTH,
    )
    if not fm.get("date"):
        fm["date"] = _infer_date(stem)
    if "summary" in fm:
        fm["summary"] = _plain_text(
            fm["summary"],
            "summary",
            filename,
            max_length=MAX_SUMMARY_LENGTH,
        )
    if "cover" in fm:
        fm["cover"] = _plain_text(fm["cover"], "cover", filename, max_length=2048)
    if "pinned" in fm:
        fm["pinned"] = _normalize_bool(fm["pinned"], "pinned", filename)
    _normalize_mini(fm, slug, filename)
    return slug, fm, body


def _resolve_slug(explicit: str, stem: str, title: str, filename: str) -> str:
    """按 显式 slug → 文件名 → 标题 → 稳定哈希 的顺序生成合法标识。"""
    if explicit:
        candidate = _slugify(explicit)
        if content.SLUG_RE.match(candidate):
            return candidate
        raise ValueError(f"{filename}: 非法标识 {explicit!r}（仅允许小写字母/数字/中划线）")
    for source in (stem, title):
        candidate = _slugify(source)
        if content.SLUG_RE.match(candidate):
            return candidate
    digest = hashlib.sha256(filename.encode("utf-8")).hexdigest()[:10]
    return f"post-{digest}"


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug[:64].strip("-")


def _infer_title(stem: str, body: str) -> str:
    """无 frontmatter title 时，优先取首个 # 标题，否则用文件名。"""
    m = re.search(r"(?m)^#\s+(.+?)\s*$", body)
    if m:
        return m.group(1).strip()
    cleaned = re.sub(r"^\d{4}[-_]?\d{2}[-_]?\d{2}[-_]?", "", stem).strip("- ")
    return cleaned or stem


def _infer_date(stem: str) -> str:
    """无 frontmatter date 时，从 YYYY-MM-DD / YYYYMMDD 前缀文件名推断。"""
    m = re.match(r"^(\d{4})[-_]?(\d{2})[-_]?(\d{2})", stem)
    if m:
        try:
            return date(
                int(m.group(1)), int(m.group(2)), int(m.group(3))
            ).isoformat()
        except ValueError:
            pass
    return date.today().isoformat()


def extract_zip(data: bytes) -> tuple[list[tuple[str, bytes]], list[str]]:
    """从 ZIP 中取出全部 Markdown 文件（扁平化，校验路径安全与大小）。

    返回 (entries, errors)：不合规的单个条目直接跳过并记入 errors，
    不中断其余条目的提取；仅 ZIP 容器本身无法解析时抛 ValueError。
    """
    out: list[tuple[str, bytes]] = []
    errors: list[str] = []
    total = 0
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ValueError("ZIP 文件无法解析") from exc
    with zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts:
                errors.append(f"ZIP 含非法路径，已跳过: {name}")
                continue
            if not name.lower().endswith(MD_SUFFIXES):
                continue
            if info.file_size > settings.import_max_file_bytes:
                errors.append(f"{name} 超过单文件大小限制，已跳过")
                continue
            if len(out) >= settings.import_max_files:
                errors.append(f"ZIP 内 Markdown 文件数量超过限制，其余已跳过")
                break
            total += info.file_size
            if total > settings.import_max_zip_bytes:
                errors.append("ZIP 解压后超过大小限制，后续文件已跳过")
                break
            try:
                out.append((p.name, zf.read(info)))
            except (RuntimeError, NotImplementedError) as exc:
                errors.append(f"{name}: 无法读取（加密或损坏），已跳过")
    return out, errors


def import_posts(
    entries: list[tuple[str, bytes]], overwrite: bool = False
) -> dict:
    """写入文章并返回 {imported, skipped, errors}。

    每个文件独立校验：不符合导入要求的条目逐项跳过并记入 errors，
    不中断其余文件的导入；超过单次数量上限时仅处理前 N 个并记录提示。
    """
    result = {
        "imported": 0,
        "skipped": 0,
        "errors": [],
        "files": [],
        "skipped_files": [],
    }

    def skip(filename: str, reason: str) -> None:
        result["skipped"] += 1
        result["skipped_files"].append({"filename": filename, "reason": reason})

    if len(entries) > settings.import_max_files:
        result["errors"].append(
            f"超过单次导入数量上限（{settings.import_max_files}），其余文件已跳过"
        )
        entries = entries[: settings.import_max_files]
    seen = set()
    for filename, data in entries:
        if not filename.strip():
            result["errors"].append("缺少文件名")
            continue
        if not filename.lower().endswith(MD_SUFFIXES):
            result["errors"].append(f"{filename}: 不支持的文件类型")
            continue
        if PurePosixPath(filename).stem in SKIP_STEMS or filename.startswith("."):
            skip(filename, "系统索引或隐藏文件")
            continue
        if len(data) > settings.import_max_file_bytes:
            result["errors"].append(f"{filename}: 超过单文件大小限制")
            continue
        try:
            text = data.decode("utf-8-sig")
            if "\x00" in text:
                raise ValueError("文件包含 NUL 控制字符")
            if not text.strip():
                result["errors"].append(f"{filename}: 文件内容为空，已跳过")
                continue
            slug, fm, body = parse_document(filename, text)
        except UnicodeDecodeError:
            result["errors"].append(f"{filename}: 不是有效的 UTF-8 文本")
            continue
        except ValueError as exc:
            result["errors"].append(str(exc))
            continue
        if slug in seen:
            skip(filename, f"本批次已存在相同标识：{slug}")
            continue
        seen.add(slug)
        if content.markdown_exists("posts", slug) and not overwrite:
            skip(filename, f"目标标识已存在且未勾选覆盖同名：{slug}")
            continue
        try:
            content.write_markdown("posts", slug, fm, body)
        except ValueError as exc:
            result["errors"].append(f"{filename}: {exc}")
            continue
        result["imported"] += 1
        result["files"].append(
            {
                "filename": filename,
                "slug": slug,
                "title": fm.get("title", slug),
                "date": str(fm.get("date", "")),
                "tags": fm.get("tags") or [],
            }
        )
    return result
