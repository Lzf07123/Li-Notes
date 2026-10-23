"""内容读写层：Markdown/YAML 文件是唯一事实来源，路径一律防穿越。"""

import html
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
import yaml

from admin.config import settings

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
IMAGE_REF_PATTERNS = (
    # Markdown 行内图片：![alt](url)、![alt](<url>)、![alt](url "title")
    lambda url: re.compile(
        r"!\[[^\]]*\]\(\s*(?:<)?" + re.escape(url) + r"(?:>)?(?:\s+[\"'][^\"']*[\"'])?\s*\)"
    ),
    # HTML <img> 标签
    lambda url: re.compile(
        r"<img\b[^>]*\bsrc\s*=\s*[\"']" + re.escape(url) + r"[\"'][^>]*>",
        re.IGNORECASE,
    ),
    # Hugo figure 短代码
    lambda url: re.compile(
        r"\{\{<\s*figure\b[^>]*\bsrc\s*=\s*[\"']" + re.escape(url) + r"[\"'][^>]*>\}\}",
        re.IGNORECASE,
    ),
)
_DANGEROUS_SVG_RE = re.compile(
    r"(<script|javascript:|data:\s*text/html|on[a-z]+\s*=)", re.IGNORECASE
)
_UNSAFE_HTML_TAG_RE = re.compile(
    r"<\s*(script|iframe|object|embed|form|base|meta|link|style|template|math|svg)\b",
    re.IGNORECASE,
)
_UNSAFE_HTML_EVENT_RE = re.compile(r"\son[a-z][a-z0-9_:-]*\s*=", re.IGNORECASE)
_UNSAFE_HTML_URL_RE = re.compile(
    r"(?:href|src|srcset|poster|action|formaction)=[\"']?"
    r"(?:javascript|vbscript|data):",
    re.IGNORECASE,
)
_UNSAFE_HTML_SRCDOC_RE = re.compile(r"\bsrcdoc\s*=", re.IGNORECASE)
_UNSAFE_HTML_STYLE_RE = re.compile(r"\sstyle\s*=", re.IGNORECASE)
_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)",
    re.DOTALL,
)


def sanitize_inline_svg(value: str) -> str:
    """清洗后台可写的内联 SVG：拒绝脚本/事件属性，保留纯展示 SVG。"""
    if not isinstance(value, str) or not value.lstrip().lower().startswith("<svg"):
        return value
    cleaned = re.sub(
        r"\son[a-z]+\s*=\s*(?:\"[^\"]*\"|'[^']*')", "", value, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if _DANGEROUS_SVG_RE.search(cleaned):
        return ""
    return cleaned


def scan_markdown_security(body: str) -> list[str]:
    """扫描 Markdown 中会被 Hugo 原样输出的危险 HTML；忽略代码围栏与行内代码。"""
    errors: list[str] = []
    fence_char = ""
    visible_lines: list[str] = []
    for line_no, line in enumerate(str(body or "").splitlines(), 1):
        fence = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)
            if not fence_char:
                fence_char = marker[0]
            elif marker[0] == fence_char:
                fence_char = ""
            continue
        if fence_char:
            continue
        visible = re.sub(r"(`+)(.*?)\1", "", line)
        visible_lines.append(visible)
        decoded = html.unescape(visible)
        tag = _UNSAFE_HTML_TAG_RE.search(decoded)
        if tag:
            errors.append(f"第 {line_no} 行禁止原始 HTML 标签 <{tag.group(1).lower()}>")
        event = _UNSAFE_HTML_EVENT_RE.search(decoded)
        if event:
            errors.append(f"第 {line_no} 行禁止内联事件属性 {event.group(0).strip()}")
        if _UNSAFE_HTML_SRCDOC_RE.search(decoded):
            errors.append(f"第 {line_no} 行禁止 srcdoc 属性")
        if _UNSAFE_HTML_STYLE_RE.search(decoded):
            errors.append(f"第 {line_no} 行禁止内联 style 属性")
    combined = re.sub(
        r"[\x00-\x20]+",
        "",
        html.unescape("\n".join(visible_lines)),
    )
    if _UNSAFE_HTML_URL_RE.search(combined):
        errors.append("禁止 javascript/data/vbscript URL")
    return errors


def split_frontmatter(text: str) -> tuple[str, str]:
    """按独立 --- 行切分 frontmatter，忽略代码/字符串中出现的 ---。"""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end():]


def safe_resolve(root: Path, rel: str) -> Path:
    root_r = root.resolve()
    p = (root_r / rel).resolve()
    if not p.is_relative_to(root_r):
        raise ValueError("path escape")
    return p


def atomic_write_text(path: Path, text: str) -> None:
    """原子写入后台可变内容，并在替换前后同步文件与目录元数据。

    配置和 Markdown 是跨容器重建仍要保留的唯一事实源。临时文件与目标位于
    同一目录，flush + fsync 后再 os.replace，避免进程中断留下半截文件。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_mode = path.stat().st_mode & 0o777 if path.exists() else None
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if previous_mode is not None:
            os.chmod(tmp, previous_mode)
        os.replace(tmp, path)
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            dir_fd = None
        if dir_fd is not None:
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass

def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fm_text, _ = split_frontmatter(text)
    if fm_text:
        try:
            return yaml.safe_load(fm_text) or {}
        except yaml.YAMLError:
            return {}
    return {}


def list_markdown(
    section: str,
    q: str = "",
    status: str = "",
    tag: str = "",
    pinned: str = "",
    sort: str = "",
    order: str = "asc",
) -> list[dict]:
    directory = settings.content_root / section
    if not directory.exists():
        return []
    items = []
    for p in sorted(directory.glob("*.md")):
        if p.stem in ("_index", "index"):
            continue
        fm = _read_frontmatter(p)
        items.append(
            {
                "slug": p.stem,
                "title": fm.get("title", p.stem),
                "date": fm.get("date", ""),
                "status": fm.get("status", "published"),
                "tags": fm.get("tags") or [],
                "pinned": bool(fm.get("pinned", False)),
                "href": fm.get("href", ""),
                "description": fm.get("description", ""),
                "weight": fm.get("weight", 0),
                "mtime": p.stat().st_mtime,
            }
        )
    if q:
        ql = q.lower()
        items = [
            it
            for it in items
            if ql in it["title"].lower()
            or ql in it["slug"].lower()
            or ql in str(it.get("href") or "").lower()
            or ql in str(it.get("description") or "").lower()
            or any(ql in str(t).lower() for t in it["tags"])
        ]
    if status and section == "posts" and status in ("published", "draft"):
        items = [it for it in items if it["status"] == status]
    if tag and section == "posts":
        tag_l = tag.strip().lower()
        items = [
            it
            for it in items
            if any(str(t).strip().lower() == tag_l for t in it["tags"])
        ]
    if section == "posts" and pinned == "1":
        items = [it for it in items if it["pinned"]]
    elif section == "posts" and pinned == "0":
        items = [it for it in items if not it["pinned"]]
    if sort in ("title", "date", "status", "slug", "href", "weight"):
        reverse = order == "desc"

        def sort_key(item):
            value = item.get(sort)
            if sort == "weight":
                try:
                    return int(value or 0)
                except (TypeError, ValueError):
                    return 0
            return (str(value or "")).lower()

        items.sort(key=sort_key, reverse=reverse)
    return items


def all_tags() -> list[str]:
    """聚合文章栏目现有标签，供编辑器自动补全。"""
    tags: set[str] = set()
    for item in list_markdown("posts"):
        tags.update(str(t) for t in (item.get("tags") or []))
    return sorted(tags)


def read_markdown(section: str, slug: str) -> tuple[dict, str]:
    if not SLUG_RE.match(slug):
        raise ValueError("bad slug")
    p = safe_resolve(settings.content_root, f"{section}/{slug}.md")
    text = p.read_text(encoding="utf-8")
    fm_text, body = split_frontmatter(text)
    if fm_text:
        try:
            return yaml.safe_load(fm_text) or {}, body.lstrip("\n")
        except yaml.YAMLError:
            return {}, text
    return {}, text


def markdown_exists(section: str, slug: str) -> bool:
    if not SLUG_RE.match(slug):
        return False
    return safe_resolve(settings.content_root, f"{section}/{slug}.md").exists()


def write_markdown(section: str, slug: str, frontmatter: dict, body: str) -> None:
    if not SLUG_RE.match(slug):
        raise ValueError("bad slug")
    fm = dict(frontmatter)
    if section == "posts":
        # Hugo 只认 draft: true，后台以 status: draft 管理草稿；两者必须保持一致，
        # 否则草稿会被渲染进公开产物并被构建自检拦截。
        fm["draft"] = fm.get("status") == "draft"
    fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
    text = f"---\n{fm}\n---\n\n{body.strip()}\n"
    p = safe_resolve(settings.content_root, f"{section}/{slug}.md")
    atomic_write_text(p, text)


def delete_markdown(section: str, slug: str) -> None:
    if not SLUG_RE.match(slug):
        raise ValueError("bad slug")
    p = safe_resolve(settings.content_root, f"{section}/{slug}.md")
    if p.exists():
        p.unlink()


def trash_markdown(section: str, slug: str) -> None:
    """把文章移入回收站（data/trash/<section>/），支持跨文件系统移动。"""
    if not SLUG_RE.match(slug):
        raise ValueError("bad slug")
    p = safe_resolve(settings.content_root, f"{section}/{slug}.md")
    if not p.exists():
        raise FileNotFoundError("文件不存在")
    trash_dir = settings.db_path.parent / "trash" / section
    trash_dir.mkdir(parents=True, exist_ok=True)
    target = trash_dir / f"{slug}.md"
    if target.exists():
        target = trash_dir / f"{slug}-{int(time.time())}.md"
    shutil.move(str(p), str(target))


def list_trash() -> list[dict]:
    """列出回收站内容：section、slug、原标题、移入时间。"""
    trash_root = settings.db_path.parent / "trash"
    if not trash_root.exists():
        return []
    items = []
    for section_dir in sorted(trash_root.iterdir()):
        if not section_dir.is_dir():
            continue
        section = section_dir.name
        for p in sorted(section_dir.glob("*.md")):
            fm = _read_frontmatter(p)
            items.append(
                {
                    "section": section,
                    "slug": p.stem,
                    "title": fm.get("title") or p.stem,
                    "mtime": p.stat().st_mtime,
                }
            )
    items.sort(key=lambda it: it["mtime"], reverse=True)
    return items


def restore_trash(section: str, slug: str) -> str:
    """把回收站文件恢复到原栏目，返回恢复后的 slug（含时间戳时截断）。"""
    trash_dir = settings.db_path.parent / "trash" / section
    candidates = [trash_dir / f"{slug}.md"]
    if not any(c.exists() for c in candidates):
        # slug 可能带时间戳后缀，按前缀匹配
        if trash_dir.exists():
            candidates = [
                p
                for p in trash_dir.glob("*.md")
                if p.stem == slug or p.stem.startswith(slug + "-")
            ]
    if not candidates or not any(c.exists() for c in candidates):
        raise FileNotFoundError("回收站中不存在该文件")
    src = next(c for c in candidates if c.exists())
    # 回收站文件名可能带 10 位 unix 时间戳后缀（旧命名），恢复时剥离；
    # 不再按首个连字符截断，避免多词 slug（my-post）被截成 my
    clean_slug = re.sub(r"-(1\d{9})$", "", src.stem)
    if not SLUG_RE.match(clean_slug):
        raise ValueError("bad slug")
    target = safe_resolve(settings.content_root, f"{section}/{clean_slug}.md")
    if target.exists():
        raise ValueError("同名文件已存在，请先处理后再恢复")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(target))
    return clean_slug


def empty_trash() -> int:
    """清空回收站，返回删除的文件数。"""
    trash_root = settings.db_path.parent / "trash"
    if not trash_root.exists():
        return 0
    count = sum(1 for p in trash_root.rglob("*.md") if p.is_file())
    shutil.rmtree(trash_root)
    return count


def remove_image_references(rel: str) -> list[str]:
    """删除媒体后，扫描内容 Markdown 并移除引用该图片的地址。

    返回被修改文件的相对路径（相对 content/）。
    """
    url = f"/img/{rel}"
    changed = []
    root = settings.content_root
    if not root.exists():
        return changed
    for p in sorted(root.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        new_text = _strip_image_refs(text, url)
        new_text = _strip_frontmatter_refs(new_text, url)
        if new_text != text:
            atomic_write_text(p, new_text)
            changed.append(p.relative_to(root).as_posix())
    return changed


def _strip_frontmatter_refs(text: str, url: str) -> str:
    """清空 Markdown frontmatter 中等于目标图片地址的字段（如 cover）。"""
    fm_text, body = split_frontmatter(text)
    if not fm_text:
        return text
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return text
    if not isinstance(fm, dict) or not _clear_matching_strings(fm, url):
        return text
    new_fm = yaml.safe_dump(
        fm, allow_unicode=True, sort_keys=False, default_flow_style=False
    ).strip()
    return f"---\n{new_fm}\n---{body}"


def _strip_image_refs(text: str, url: str) -> str:
    for make_pattern in IMAGE_REF_PATTERNS:
        text = make_pattern(url).sub("", text)
    return text


def _clear_matching_strings(node, target: str) -> bool:
    """递归把 YAML 中等于 target 的字符串值清空，返回是否有修改。"""
    changed = False
    if isinstance(node, dict):
        for key, value in list(node.items()):
            if isinstance(value, str) and value == target:
                node[key] = ""
                changed = True
            elif isinstance(value, (dict, list)):
                changed = _clear_matching_strings(value, target) or changed
    elif isinstance(node, list):
        for i, value in enumerate(node):
            if isinstance(value, str) and value == target:
                node[i] = ""
                changed = True
            elif isinstance(value, (dict, list)):
                changed = _clear_matching_strings(value, target) or changed
    return changed


def clear_config_image_refs(rel: str) -> list[str]:
    """删除媒体后，清空 config/*.yaml 中引用该图片的字段。返回修改的文件名。"""
    url = f"/img/{rel}"
    changed = []
    root = settings.config_root
    if not root.exists():
        return changed
    for p in sorted(root.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict) or not _clear_matching_strings(data, url):
            continue
        text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
        atomic_write_text(p, f"# {p.stem}.yaml（后台保存生成）\n{text}")
        changed.append(p.name)
    return changed


def load_yaml(name: str) -> dict:
    p = safe_resolve(settings.config_root, f"{name}.yaml")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def save_yaml(name: str, data: dict) -> None:
    p = safe_resolve(settings.config_root, f"{name}.yaml")
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    atomic_write_text(p, f"# {name}.yaml（后台保存生成）\n{text}")
