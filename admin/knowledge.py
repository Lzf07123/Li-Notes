"""小程序速查内容导出：文章 frontmatter 是唯一内容源。"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
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
MAX_PAYLOAD_CHARS = 512 * 1024
TEXT_FIELDS = ("title", "command", "summary", "syntax")
AUTO_GENERATOR = "auto-scrape-v1"
DEFAULT_AUTO_LANGUAGES = ["bash", "shell", "sh", "console", "yaml"]
DEFAULT_CATEGORY_TERMS = {
    "linux": ["linux", "bash", "shell", "apt", "dpkg", "rpm", "dnf", "yum", "pacman", "命令"],
    "kubernetes": ["kubernetes", "k8s", "kubectl", "pod", "集群", "容器云", "helm", "ingress", "prometheus"],
    "markdown": ["markdown", "frontmatter", "hugo", "写作"],
}


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


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _as_int(value: Any, field: str, default: int, minimum: int, maximum: int) -> int:
    if value in (None, ""):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} 必须是整数") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{field} 必须在 {minimum}-{maximum} 之间")
    return number


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


def _coerce_text_list(
    value: Any,
    field: str,
    limit: int = MAX_LIST,
    default: list[str] | None = None,
) -> list[str]:
    if value is None:
        return list(default or [])
    if isinstance(value, str):
        value = [part.strip() for part in value.split(",") if part.strip()]
    return _text_list(value, field, limit=limit) or list(default or [])


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
        label = _text(raw.get("label"), f"categories[{index}].label", required=True, max_len=40)
        fallback_terms = [category_id, label, *DEFAULT_CATEGORY_TERMS.get(category_id, [])]
        match_terms = _coerce_text_list(
            raw.get("match_terms"),
            f"categories[{index}].match_terms",
            default=fallback_terms,
        )
        deduped_terms = []
        term_seen = set()
        for term in match_terms:
            key = term.casefold()
            if key not in term_seen:
                term_seen.add(key)
                deduped_terms.append(term)
        normalized.append(
            {
                "id": category_id,
                "label": label,
                "intro": _text(raw.get("intro"), f"categories[{index}].intro", max_len=120),
                "symbol": _text(raw.get("symbol"), f"categories[{index}].symbol", max_len=4),
                "match_terms": deduped_terms,
            }
        )

    auto_raw = data.get("auto_scrape") if isinstance(data.get("auto_scrape"), dict) else {}
    default_category = _text(
        auto_raw.get("default_category"), "auto_scrape.default_category", max_len=32
    )
    if default_category and default_category not in seen:
        raise ValueError(f"auto_scrape.default_category 使用了未知分类：{default_category}")
    auto_scrape = {
        "enabled": _as_bool(auto_raw.get("enabled"), default=True),
        "default_category": default_category,
        "include_languages": _coerce_text_list(
            auto_raw.get("include_languages"),
            "auto_scrape.include_languages",
            default=DEFAULT_AUTO_LANGUAGES,
        ),
        "max_items_per_article": _as_int(
            auto_raw.get("max_items_per_article"),
            "auto_scrape.max_items_per_article",
            3,
            1,
            20,
        ),
        "max_examples": _as_int(
            auto_raw.get("max_examples"),
            "auto_scrape.max_examples",
            3,
            1,
            10,
        ),
        "max_code_chars": _as_int(
            auto_raw.get("max_code_chars"),
            "auto_scrape.max_code_chars",
            6000,
            200,
            MAX_CODE,
        ),
        "min_code_chars": _as_int(
            auto_raw.get("min_code_chars"),
            "auto_scrape.min_code_chars",
            8,
            1,
            2000,
        ),
    }
    min_app_version = _text(data.get("min_app_version"), "min_app_version", max_len=32) or "0.2.0"
    return {
        "schema_version": int(data.get("schema_version") or SCHEMA_VERSION),
        "min_app_version": min_app_version,
        "categories": normalized,
        "auto_scrape": auto_scrape,
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
    if not _as_bool(mini.get("enabled"), default=False):
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
    result = {"enabled": True, "items": normalized}
    generated_by = _text(mini.get("generated_by"), "mini.generated_by", max_len=48)
    if generated_by:
        result["generated_by"] = generated_by
    return result


def _article_url(base_url: str, slug: str) -> str:
    path = f"posts/{slug}/"
    if base_url:
        return urljoin(base_url.rstrip("/") + "/", path)
    return f"/{path}"


def _clean_markdown(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(
        r"</?(?:br|p|div|span|strong|em|code|a)\b[^>]*>",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"[`*_~]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clip(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def _h2_sections(body: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading = ""
    lines: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        match = None if in_fence else re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            if heading:
                sections.append((heading, "\n".join(lines)))
            heading = match.group(1).strip()
            lines = []
        elif heading:
            lines.append(line)
    if heading:
        sections.append((heading, "\n".join(lines)))
    return sections


def _headings(body: str) -> list[str]:
    result = []
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^#{2,3}\s+(.+?)\s*$", line)
        if match:
            result.append(match.group(1).strip())
    return result


def _iter_code_blocks(body: str) -> list[dict]:
    blocks: list[dict] = []
    heading2 = ""
    heading3 = ""
    in_fence = False
    language = ""
    code_lines: list[str] = []
    for line in body.splitlines():
        fence = re.match(r"^\s*```([^`]*)$", line)
        if fence:
            if not in_fence:
                in_fence = True
                language = fence.group(1).strip().lower().split()[0] if fence.group(1).strip() else ""
                code_lines = []
            else:
                blocks.append(
                    {
                        "language": language,
                        "heading": heading3 or heading2,
                        "h2": heading2,
                        "h3": heading3,
                        "code": "\n".join(code_lines).strip(),
                    }
                )
                in_fence = False
                language = ""
                code_lines = []
            continue
        if in_fence:
            code_lines.append(line)
            continue
        match = re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if match:
            if len(match.group(1)) == 2:
                heading2 = match.group(2).strip()
                heading3 = ""
            else:
                heading3 = match.group(2).strip()
    return blocks


def _first_paragraph(body: str) -> str:
    in_fence = False
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        if (
            line.startswith(("#", "|", "-", "*", ">", "<", "![", "---"))
            or re.match(r"^\d+[.)]\s", line)
        ):
            continue
        cleaned = _clean_markdown(line)
        if len(cleaned) >= 8:
            return _clip(cleaned, 600)
    return ""


def _goal_notes(body: str) -> list[str]:
    for heading, content in _h2_sections(body):
        if "今日目标" not in heading and "学习目标" not in heading:
            continue
        notes = []
        for line in content.splitlines():
            match = re.match(r"^\s*[-*]\s+(?:\[[ xX]\]\s*)?(.+?)\s*$", line)
            if not match:
                continue
            note = _clean_markdown(match.group(1))
            if note:
                notes.append(_clip(note, 300))
            if len(notes) >= 5:
                break
        return notes
    return []


def _split_table_row(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|") and not value.endswith("\\|"):
        value = value[:-1]
    cells = re.split(r"(?<!\\)\|", value)
    return [_clean_markdown(cell.replace("\\|", "|")) for cell in cells]


def _table_rows(content: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in content.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []
    header = _split_table_row(lines[0])
    separator = _split_table_row(lines[1])
    if not separator or not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in separator):
        return []
    rows = []
    for line in lines[2:]:
        cells = _split_table_row(line)
        if not any(cells):
            continue
        rows.append({str(index): value for index, value in enumerate(cells)})
    if rows:
        rows.insert(0, {"__header__": "|".join(header)})
    return rows


def _command_table(body: str) -> list[dict[str, str]]:
    for heading, content in _h2_sections(body):
        rows = _table_rows(content)
        if not rows:
            continue
        header = rows[0].get("__header__", "").casefold()
        heading_hint = heading.casefold()
        if "命令" in header or "command" in header or "命令速查" in heading_hint:
            return rows[1:]
    return []


def _unique(values: list[str], limit: int = MAX_LIST) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = _clean_markdown(value)
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(_clip(text, 120))
        if len(result) >= limit:
            break
    return result


def _command_name(command: str) -> str:
    for token in command.split():
        clean = token.strip("`'\"")
        if clean in ("sudo", "env") or clean.startswith("-"):
            continue
        if clean.endswith(":") or "=" in clean and not clean.startswith("--"):
            continue
        return _clip(clean, 80)
    return _clip(command.split()[0] if command.split() else "示例", 80)


def _first_command(code: str) -> str:
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^\$\s*", "", line)
        if line in ("---", "...") or re.match(r"^[A-Za-z0-9_.-]+:\s", line):
            continue
        return _clip(line, 4000)
    return ""


def _infer_category(
    config: dict,
    slug: str,
    title: str,
    tags: list[str],
    headings: list[str],
) -> str:
    tag_text = " ".join(tags).casefold()
    title_text = f"{slug} {title}".casefold()
    heading_text = " ".join(headings).casefold()
    best_id = ""
    best_score = 0
    for category in config["categories"]:
        score = 0
        for term in category.get("match_terms") or []:
            needle = str(term).strip().casefold()
            if not needle:
                continue
            if needle in tag_text:
                score += 10
            elif needle in title_text:
                score += 4
            elif needle in heading_text:
                score += 1
        if score > best_score:
            best_id = category["id"]
            best_score = score
    if best_id:
        return best_id
    return str(config.get("auto_scrape", {}).get("default_category") or "")


def _auto_id(slug: str, number: int) -> str:
    suffix = f"-auto-{number}"
    base = slug[: max(1, 64 - len(suffix))].strip("-")
    return f"{base}{suffix}"


def _table_items(
    rows: list[dict[str, str]],
    category: str,
    tags: list[str],
    title: str,
    limit: int,
) -> list[dict]:
    items = []
    for row in rows:
        command = _clean_markdown(row.get("0", ""))
        function = _clean_markdown(row.get("1", ""))
        note = _clean_markdown(row.get("2", ""))
        if not command:
            continue
        if not function:
            function = command
        item_title = function
        if item_title.casefold() in (command.casefold(), title.casefold()):
            item_title = f"{title} · {len(items) + 1}"
        summary = function
        if note and note.casefold() not in function.casefold():
            summary = f"{function}：{note}"
        items.append(
            {
                "category": category,
                "title": _clip(item_title, 120),
                "command": _clip(command, 200),
                "summary": _clip(summary, 1000),
                "syntax": _clip(command, 4000),
                "keywords": _unique([*tags, _command_name(command)]),
                "tags": _unique(tags, 20),
                "examples": [{"label": _clip(function or "执行命令", 200), "code": _clip(command, 12000)}],
                "notes": [_clip(note, 1000)] if note else [],
                "related": [],
                "order": 100 + len(items),
            }
        )
        if len(items) >= limit:
            break
    return items


def _code_item(
    blocks: list[dict],
    category: str,
    tags: list[str],
    title: str,
    summary: str,
    goals: list[str],
    max_examples: int,
    max_code_chars: int,
) -> dict | None:
    examples = []
    for index, block in enumerate(blocks[:max_examples], 1):
        code = _clip(str(block.get("code") or "").strip(), max_code_chars)
        if not code:
            continue
        label = _clean_markdown(block.get("heading") or f"示例 {index}")
        examples.append({"label": _clip(label or f"示例 {index}", 200), "code": code})
    if not examples:
        return None
    syntax = _first_command(examples[0]["code"])
    if not syntax:
        return None
    return {
        "category": category,
        "title": title,
        "command": _command_name(syntax),
        "summary": summary,
        "syntax": syntax,
        "keywords": _unique([*tags, _command_name(syntax)]),
        "tags": _unique(tags, 20),
        "examples": examples,
        "notes": goals[:3],
        "related": [],
        "order": 100,
    }


def scrape_article(
    slug: str,
    frontmatter: dict,
    body: str,
    config: dict,
) -> tuple[dict | None, str]:
    """从一篇 Markdown 中确定性抽取小程序速查候选。"""
    settings = config["auto_scrape"]
    title = _clean_markdown(frontmatter.get("title") or slug)
    tags = _text_list(frontmatter.get("tags"), "文章 tags")
    headings = _headings(body)
    category = _infer_category(config, slug, title, tags, headings)
    if not category:
        return None, "未匹配知识分类"
    summary = _clean_markdown(frontmatter.get("summary") or frontmatter.get("description"))
    if not summary:
        summary = _first_paragraph(body)
    if not summary:
        summary = f"来自《{title}》的自动速查候选。"
    rows = _command_table(body)
    items = _table_items(rows, category, tags, title, settings["max_items_per_article"])
    if not items:
        allowed = {str(x).casefold() for x in settings["include_languages"]}
        blocks = [
            block
            for block in _iter_code_blocks(body)
            if block.get("language", "") in allowed
            and len(str(block.get("code") or "").strip()) >= settings["min_code_chars"]
        ]
        item = _code_item(
            blocks,
            category,
            tags,
            title,
            summary,
            _goal_notes(body),
            settings["max_examples"],
            settings["max_code_chars"],
        )
        items = [item] if item else []
    if not items:
        return None, "未找到可抽取的命令表格或代码块"
    for index, item in enumerate(items, 1):
        item["id"] = _auto_id(slug, index)
    mini = {"enabled": True, "generated_by": AUTO_GENERATOR, "items": items}
    return validate_mini_config(mini, slug, tags), ""


def scan_articles(
    root: Path,
    base_url: str = "",
    now: dt.datetime | None = None,
) -> dict:
    """扫描文章，返回后台预览与构建共用的确定性同步报告。"""
    now = now or dt.datetime.now().astimezone()
    config = load_config(root)
    auto_enabled = config["auto_scrape"]["enabled"]
    records: list[dict] = []
    for path in sorted((root / "content" / "posts").glob("*.md")):
        if path.stem in ("_index", "index"):
            continue
        fm = _read_frontmatter(path)
        if not fm:
            continue
        title = str(fm.get("title") or path.stem)
        status = str(fm.get("status") or "published")
        date_text = str(fm.get("date") or "")[:10]
        if fm.get("draft") is True or status != "published":
            records.append(
                {
                    "slug": path.stem,
                    "title": title,
                    "status": "skipped",
                    "reason": "草稿或未发布",
                    "items": [],
                }
            )
            continue
        try:
            if date_text and dt.date.fromisoformat(date_text) > now.date():
                records.append(
                    {
                        "slug": path.stem,
                        "title": title,
                        "status": "skipped",
                        "reason": "未来文章",
                        "items": [],
                    }
                )
                continue
        except ValueError:
            pass
        raw_text = path.read_text(encoding="utf-8")
        _fm_text, body = split_frontmatter(raw_text)
        raw_mini = fm.get("mini_json")
        has_mini = raw_mini not in (None, "", {})
        if has_mini:
            mini = validate_mini_config(
                parse_mini_field(raw_mini), path.stem, fm.get("tags") or []
            )
            if not mini.get("enabled"):
                records.append(
                    {
                        "slug": path.stem,
                        "title": title,
                        "status": "skipped",
                        "reason": "文章显式关闭小程序同步",
                        "items": [],
                    }
                )
                continue
            mode = "generated" if mini.get("generated_by") == AUTO_GENERATOR else "manual"
            reason = ""
        else:
            if not auto_enabled:
                records.append(
                    {
                        "slug": path.stem,
                        "title": title,
                        "status": "skipped",
                        "reason": "自动刮削已关闭",
                        "items": [],
                    }
                )
                continue
            mini, reason = scrape_article(path.stem, fm, body, config)
            mode = "auto"
            if not mini:
                records.append(
                    {
                        "slug": path.stem,
                        "title": title,
                        "status": "skipped",
                        "reason": reason,
                        "items": [],
                    }
                )
                continue
        preview_items = [
            {
                "id": item["id"],
                "title": item["title"],
                "command": item["command"],
                "category": item["category"],
            }
            for item in mini["items"]
        ]
        records.append(
            {
                "slug": path.stem,
                "title": title,
                "status": mode,
                "reason": "",
                "category": (
                    mini["items"][0]["category"] if mini.get("items") else ""
                ),
                "item_count": len(preview_items),
                "items": preview_items,
                "mini": mini,
                "updated": str(fm.get("updated") or fm.get("date") or "")[:10],
            }
        )

    active = [record for record in records if record.get("mini")]
    return {
        "config": config,
        "records": records,
        "total": len([r for r in records if r.get("status") != "skipped"]),
        "manual": len([r for r in active if r.get("status") == "manual"]),
        "generated": len([r for r in active if r.get("status") == "generated"]),
        "auto": len([r for r in active if r.get("status") == "auto"]),
        "skipped": len([r for r in records if r.get("status") == "skipped"]),
        "manual_items": sum(r.get("item_count", 0) for r in active if r.get("status") == "manual"),
        "generated_items": sum(
            r.get("item_count", 0) for r in active if r.get("status") == "generated"
        ),
        "auto_items": sum(r.get("item_count", 0) for r in active if r.get("status") == "auto"),
    }


def build_bundle(
    root: Path,
    base_url: str = "",
    now: dt.datetime | None = None,
) -> tuple[dict, dict, str]:
    """扫描文章并生成 (manifest, payload, canonical_data_json)。"""
    now = now or dt.datetime.now().astimezone()
    report = scan_articles(root, base_url=base_url, now=now)
    config = report["config"]
    category_config = {item["id"]: item for item in config["categories"]}
    items: list[dict] = []
    seen_ids: set[str] = set()
    for record in report["records"]:
        mini = record.get("mini")
        if not mini:
            continue
        source_url = _article_url(base_url, record["slug"])
        updated = str(record.get("updated") or "")
        for item in mini["items"]:
            if item["id"] in seen_ids:
                raise ValueError(f"重复速查 id：{item['id']}")
            if item["category"] not in category_config:
                raise ValueError(f"{item['id']} 使用了未知分类：{item['category']}")
            seen_ids.add(item["id"])
            normalized = dict(item)
            normalized["source_url"] = normalized.get("source_url") or source_url
            normalized["source_title"] = _clip(str(record["title"]), 160)
            normalized["updated"] = updated
            items.append(normalized)
    if len(items) > MAX_ITEMS:
        raise ValueError(f"速查条目超过 {MAX_ITEMS} 条")
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
    if len(data_text) > MAX_PAYLOAD_CHARS:
        raise ValueError(f"knowledge payload 超过 {MAX_PAYLOAD_CHARS} 字符")
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
    previous_data_name = ""
    manifest_path = knowledge_dir / "manifest.json"
    if manifest_path.exists():
        try:
            previous_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous_url = str(previous_manifest.get("dataUrl") or "")
            if previous_url.startswith("/knowledge/"):
                candidate = Path(previous_url).name
                if candidate != "manifest.json" and (knowledge_dir / candidate).is_file():
                    previous_data_name = candidate
        except (OSError, ValueError, TypeError, UnicodeDecodeError):
            previous_data_name = ""
    data_path = output_root / manifest["dataUrl"].lstrip("/")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_tmp = data_path.with_name(data_path.name + ".tmp")
    data_tmp.write_text(data_text, encoding="utf-8")
    data_tmp.replace(data_path)
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    manifest_tmp = manifest_path.with_name("manifest.json.tmp")
    manifest_tmp.write_text(manifest_text, encoding="utf-8")
    manifest_tmp.replace(manifest_path)
    # 保留当前与上一版本，避免客户端刚取到旧 manifest 后遇到版本文件 404。
    keep = {"manifest.json", data_path.name}
    if previous_data_name:
        keep.add(previous_data_name)
    for stale in knowledge_dir.glob("*.json"):
        if stale.name not in keep:
            stale.unlink()
    return {**manifest, "manifestPath": str(manifest_path), "dataPath": str(data_path)}
