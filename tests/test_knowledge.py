import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import yaml

from admin import knowledge
from admin.content import split_frontmatter


class KnowledgeExportTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "content" / "posts").mkdir(parents=True)
        (self.root / "config").mkdir()
        (self.root / "config" / "knowledge.yaml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "min_app_version": "0.2.0",
                    "categories": [
                        {"id": "linux", "label": "Linux", "intro": "命令", "symbol": "L"}
                    ],
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _write_post(self, slug, mini, status="published", title=None):
        fm = {
            "title": title or slug,
            "date": "2026-10-23",
            "status": status,
            "tags": ["Linux", "包管理"],
        }
        if mini is not None:
            fm["mini_json"] = json.dumps(mini, ensure_ascii=False, indent=2)
        text = "---\n" + yaml.safe_dump(
            fm, allow_unicode=True, sort_keys=False
        ) + "---\n\n正文\n"
        (self.root / "content" / "posts" / f"{slug}.md").write_text(text, encoding="utf-8")

    def _mini(self, item_id="apt"):
        return {
            "enabled": True,
            "items": [
                {
                    "id": item_id,
                    "category": "linux",
                    "title": "APT",
                    "command": "apt",
                    "summary": "包管理",
                    "keywords": ["安装"],
                    "tags": ["包管理"],
                    "syntax": "apt [操作]",
                    "examples": [{"label": "更新", "code": "sudo apt update"}],
                    "notes": ["先更新索引"],
                    "related": [],
                    "order": 10,
                }
            ],
        }

    def test_frontmatter_split_ignores_dashes_inside_block_scalar(self):
        text = (
            "---\n"
            "title: T\n"
            "mini_json: |-\n"
            '  {"syntax":"| A | B |\\n| --- | --- |"}\n'
            "---\n\n"
            "body\n"
        )
        fm_text, body = split_frontmatter(text)
        self.assertIn("mini_json", fm_text)
        self.assertEqual(body.strip(), "body")

    def test_build_bundle_exports_published_mini_items(self):
        self._write_post("apt", self._mini())
        self._write_post("draft", self._mini("draft"), status="draft")
        manifest, payload, data_text = knowledge.build_bundle(
            self.root,
            base_url="https://notes.example.test/",
            now=datetime(2026, 10, 23, 12, 0, 0),
        )
        self.assertEqual(manifest["count"], 1)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["id"], "apt")
        self.assertEqual(
            payload["items"][0]["source_url"],
            "https://notes.example.test/posts/apt/",
        )
        self.assertEqual(payload["items"][0]["tags"], ["包管理"])
        self.assertEqual(payload["categories"][0]["count"], 1)
        self.assertEqual(knowledge.payload_digest(payload), manifest["sha256"])

    def test_generated_at_does_not_change_content_digest(self):
        self._write_post("apt", self._mini())
        first_manifest, first_payload, _ = knowledge.build_bundle(
            self.root, now=datetime(2026, 10, 23, 10, 0, 0)
        )
        second_manifest, second_payload, _ = knowledge.build_bundle(
            self.root, now=datetime(2026, 10, 23, 11, 0, 0)
        )
        self.assertEqual(first_manifest["contentVersion"], second_manifest["contentVersion"])
        self.assertEqual(first_manifest["sha256"], second_manifest["sha256"])
        self.assertNotEqual(first_payload["generatedAt"], second_payload["generatedAt"])
        self.assertEqual(
            knowledge.payload_digest(first_payload),
            knowledge.payload_digest(second_payload),
        )

    def test_export_bundle_writes_manifest_and_version_file(self):
        self._write_post("apt", self._mini())
        out = self.root / "output"
        result = knowledge.export_bundle(
            self.root,
            out,
            base_url="https://notes.example.test",
            now=datetime(2026, 10, 23, 12, 0, 0),
        )
        manifest_path = out / "knowledge" / "manifest.json"
        data_path = out / result["dataUrl"].lstrip("/")
        self.assertTrue(manifest_path.exists())
        self.assertTrue(data_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        self.assertEqual(knowledge.payload_digest(payload), manifest["sha256"])

    def test_duplicate_id_is_rejected(self):
        self._write_post("apt", self._mini())
        self._write_post("apt2", self._mini())
        with self.assertRaisesRegex(ValueError, "重复速查 id"):
            knowledge.build_bundle(self.root)

    def test_unknown_related_id_is_rejected(self):
        mini = self._mini()
        mini["items"][0]["related"] = ["missing"]
        self._write_post("apt", mini)
        with self.assertRaisesRegex(ValueError, "关联了不存在"):
            knowledge.build_bundle(self.root)

    def test_invalid_mini_json_is_rejected(self):
        (self.root / "content" / "posts" / "bad.md").write_text(
            "---\ntitle: Bad\ndate: 2026-10-23\nstatus: published\n"
            "mini_json: '{broken'\n---\n\n正文\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "mini_json"):
            knowledge.build_bundle(self.root)


if __name__ == "__main__":
    unittest.main()
