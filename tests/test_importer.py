import io
import json
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from admin import importer
from admin.config import settings


class TestImporter(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        settings.content_root = root / "content"
        (settings.content_root / "posts").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_parse_document_defaults(self):
        slug, fm, body = importer.parse_document(
            "hello.md", "---\ntitle: Hello\ntags: a, b\n---\n正文"
        )
        self.assertEqual(slug, "hello")
        self.assertEqual(fm["tags"], ["a", "b"])
        self.assertEqual(fm["status"], "published")
        self.assertEqual(body, "正文")

    def test_note_template_is_valid_and_importable(self):
        text = importer.template_markdown("note", today=date(2026, 10, 23))
        slug, fm, body = importer.parse_document(
            importer.TEMPLATE_KINDS["note"], text
        )
        self.assertEqual(slug, "imported-note-example")
        self.assertEqual(fm["date"], "2026-10-23")
        self.assertEqual(fm["status"], "draft")
        self.assertIn("# 示例：我的学习笔记", body)

    def test_mini_template_contains_valid_sync_config(self):
        text = importer.template_markdown("mini", today=date(2026, 10, 23))
        slug, fm, _ = importer.parse_document(
            importer.TEMPLATE_KINDS["mini"], text
        )
        mini = json.loads(fm["mini_json"])
        self.assertEqual(slug, "mini-sync-example")
        self.assertTrue(mini["enabled"])
        self.assertEqual(mini["items"][0]["id"], "mini-sync-example")
        self.assertEqual(mini["items"][0]["category"], "linux")

    def test_parse_document_normalizes_slug(self):
        slug, fm, body = importer.parse_document(
            "Bad Name.md", "---\ntitle: x\n---\n"
        )
        self.assertEqual(slug, "bad-name")
        self.assertEqual(fm["title"], "x")

    def test_parse_document_chinese_filename_falls_back_to_hash(self):
        slug, fm, _ = importer.parse_document("我的第一篇博客.md", "---\ntitle: 我的博客\n---\n")
        self.assertRegex(slug, r"^post-[a-f0-9]{10}$")
        self.assertEqual(fm["title"], "我的博客")

    def test_parse_document_explicit_slug_normalized(self):
        slug, _, _ = importer.parse_document(
            "a.md", "---\ntitle: A\nslug: My Post\n---\n"
        )
        self.assertEqual(slug, "my-post")

    def test_import_skips_index_files(self):
        result = importer.import_posts(
            [
                ("_index.md", "---\ntitle: 文章\n---\n".encode("utf-8")),
                ("index.md", "---\ntitle: 索引\n---\n".encode("utf-8")),
            ]
        )
        self.assertEqual(result["imported"], 0)
        self.assertEqual(result["skipped"], 2)

    def test_import_rejects_non_markdown(self):
        result = importer.import_posts([("a.txt", b"hello")])
        self.assertEqual(result["imported"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("不支持的文件类型", result["errors"][0])

    def test_import_rejects_blank_filename(self):
        result = importer.import_posts([("", b"---\ntitle: A\n---\n")])
        self.assertEqual(result["imported"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("缺少文件名", result["errors"][0])

    def test_import_rejects_stored_xss_payload(self):
        payload = "---\ntitle: XSS\n---\n\n<img src=x onerror=alert(1)>\n"
        result = importer.import_posts([("xss.md", payload.encode("utf-8"))])
        self.assertEqual(result["imported"], 0)
        self.assertIn("不安全 HTML", result["errors"][0])
        self.assertFalse((settings.content_root / "posts" / "xss.md").exists())

    def test_import_rejects_empty_file(self):
        result = importer.import_posts([("untitled.md", b"")])
        self.assertEqual(result["imported"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("文件内容为空", result["errors"][0])
        self.assertFalse((settings.content_root / "posts" / "untitled.md").exists())

    def test_import_rejects_invalid_utf8_without_writing(self):
        result = importer.import_posts([("bad.md", b"---\ntitle: Bad\n---\n\xff")])
        self.assertEqual(result["imported"], 0)
        self.assertIn("不是有效的 UTF-8", result["errors"][0])
        self.assertFalse((settings.content_root / "posts" / "bad.md").exists())

    def test_parse_document_rejects_invalid_date_and_status(self):
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            importer.parse_document("a.md", "---\ntitle: A\ndate: 2026-99-99\n---\n")
        with self.assertRaisesRegex(ValueError, "published 或 draft"):
            importer.parse_document("a.md", "---\ntitle: A\nstatus: secret\n---\n")

    def test_parse_document_normalizes_tags_pinned_and_mini(self):
        slug, fm, _ = importer.parse_document(
            "sync.md",
            "---\n"
            "title: Sync\n"
            "status: DRAFT\n"
            "tags: [Linux, linux, command, '']\n"
            "pinned: 'false'\n"
            'mini_json: \'{"enabled": false}\'\n'
            "---\n",
        )
        self.assertEqual(slug, "sync")
        self.assertEqual(fm["status"], "draft")
        self.assertEqual(fm["tags"], ["Linux", "command"])
        self.assertIs(fm["pinned"], False)
        self.assertEqual(json.loads(fm["mini_json"]), {"enabled": False})

    def test_parse_document_rejects_invalid_mini_config(self):
        with self.assertRaisesRegex(ValueError, "mini_json 校验失败"):
            importer.parse_document(
                "sync.md",
                "---\n"
                "title: Sync\n"
                'mini_json: \'{"enabled": true, "items": []}\'\n'
                "---\n",
            )

    def test_limits_read_from_settings(self):
        original_files = settings.import_max_files
        original_bytes = settings.import_max_file_bytes
        try:
            settings.import_max_files = 1
            result = importer.import_posts([("a.md", b"---\ntitle: A\n---\n"), ("b.md", b"x")])
            self.assertEqual(result["imported"], 1)
            self.assertTrue(
                any("超过单次导入数量上限" in err for err in result["errors"])
            )
            settings.import_max_files = original_files
            settings.import_max_file_bytes = 3
            result = importer.import_posts([("a.md", b"1234")])
            self.assertEqual(result["imported"], 0)
            self.assertIn("超过单文件大小限制", result["errors"][0])
        finally:
            settings.import_max_files = original_files
            settings.import_max_file_bytes = original_bytes

    def test_import_posts_counts(self):
        entries = [
            ("a.md", b"---\ntitle: A\n---\nAAA"),
            ("b.md", b"---\ntitle: B\n---\nBBB"),
        ]
        result = importer.import_posts(entries)
        self.assertEqual(result["imported"], 2)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["files"]), 2)
        self.assertTrue((settings.content_root / "posts" / "a.md").exists())

    def test_import_nested_folder_paths(self):
        entries = [
            ("docs/2026/a.md", b"---\ntitle: A\n---\n"),
            ("notes/sub/b.md", b"---\ntitle: B\n---\n"),
        ]
        result = importer.import_posts(entries)
        self.assertEqual(result["imported"], 2)
        self.assertTrue((settings.content_root / "posts" / "a.md").exists())
        self.assertTrue((settings.content_root / "posts" / "b.md").exists())

    def test_import_infers_metadata_without_frontmatter(self):
        result = importer.import_posts(
            [("2026-08-18-my-post.md", "# 自动标题\n\n正文".encode("utf-8"))]
        )
        self.assertEqual(result["imported"], 1)
        meta = result["files"][0]
        self.assertEqual(meta["slug"], "2026-08-18-my-post")
        self.assertEqual(meta["title"], "自动标题")
        self.assertEqual(meta["date"], "2026-08-18")
        self.assertEqual(meta["tags"], [])

    def test_infer_date_falls_back_on_invalid_date(self):
        slug, fm, _ = importer.parse_document("2026-99-99-bad.md", "正文")
        self.assertEqual(slug, "2026-99-99-bad")
        self.assertRegex(fm["date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_import_posts_skips_existing(self):
        (settings.content_root / "posts" / "a.md").write_text(
            "---\ntitle: Old\n---\nold", encoding="utf-8"
        )
        result = importer.import_posts([("a.md", b"---\ntitle: New\n---\nnew")])
        self.assertEqual(result["imported"], 0)
        self.assertEqual(result["skipped"], 1)
        self.assertIn("未勾选覆盖同名", result["skipped_files"][0]["reason"])
        self.assertIn(
            "Old", (settings.content_root / "posts" / "a.md").read_text(encoding="utf-8")
        )

    def test_import_posts_overwrite(self):
        (settings.content_root / "posts" / "a.md").write_text(
            "---\ntitle: Old\n---\nold", encoding="utf-8"
        )
        result = importer.import_posts(
            [("a.md", b"---\ntitle: New\n---\nnew")], overwrite=True
        )
        self.assertEqual(result["imported"], 1)
        self.assertIn(
            "New", (settings.content_root / "posts" / "a.md").read_text(encoding="utf-8")
        )

    def test_import_reports_duplicate_slug_reason(self):
        result = importer.import_posts(
            [
                ("first.md", b"---\ntitle: First\nslug: same-slug\n---\n"),
                ("second.md", b"---\ntitle: Second\nslug: same-slug\n---\n"),
            ]
        )
        self.assertEqual(result["imported"], 1)
        self.assertEqual(result["skipped"], 1)
        self.assertIn("本批次已存在相同标识", result["skipped_files"][0]["reason"])

    def test_import_posts_collects_errors(self):
        result = importer.import_posts(
            [("a.md", "---\ntitle: x\nslug: !!!\n---\n".encode("utf-8"))]
        )
        self.assertEqual(result["imported"], 0)
        self.assertEqual(len(result["errors"]), 1)

    def test_extract_zip_skips_traversal_keeps_safe_members(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.md", "---\ntitle: x\n---\n")
            zf.writestr("ok.md", "---\ntitle: OK\n---\n")
        entries, errors = importer.extract_zip(buf.getvalue())
        self.assertEqual([n for n, _ in entries], ["ok.md"])
        self.assertTrue(any("非法路径" in err for err in errors))

    def test_extract_zip_too_many_files_keeps_first(self):
        original = settings.import_max_files
        try:
            settings.import_max_files = 1
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr("a.md", "---\ntitle: A\n---\n")
                zf.writestr("b.md", "---\ntitle: B\n---\n")
            entries, errors = importer.extract_zip(buf.getvalue())
            self.assertEqual([n for n, _ in entries], ["a.md"])
            self.assertTrue(any("数量超过限制" in err for err in errors))
        finally:
            settings.import_max_files = original

    def test_extract_zip_returns_markdown_only(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("posts/a.md", "---\ntitle: A\n---\n")
            zf.writestr("ignore.txt", "x")
        entries, errors = importer.extract_zip(buf.getvalue())
        self.assertEqual([n for n, _ in entries], ["a.md"])
        self.assertEqual(errors, [])

    def test_import_skips_bad_entry_keeps_good(self):
        result = importer.import_posts(
            [
                ("bad.md", "---\ntitle: x\nslug: !!!\n---\n".encode("utf-8")),
                ("good.md", "---\ntitle: Good\n---\n正文".encode("utf-8")),
            ]
        )
        self.assertEqual(result["imported"], 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertTrue((settings.content_root / "posts" / "good.md").exists())


if __name__ == "__main__":
    unittest.main()
